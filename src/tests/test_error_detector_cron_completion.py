from __future__ import annotations

import tempfile
import json
import os
import subprocess
from datetime import datetime
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.cron_completion import CRON_JOB_REGISTRY, CronCompletionDetector


def test_finalization_detector_window_precedes_preopen_scanner():
    jobs = {job["id"]: job for job in CRON_JOB_REGISTRY}
    assert jobs["postclose_finalization"]["window_start"] == (5, 0)
    assert jobs["postclose_finalization"]["window_end"] == (6, 50)
    assert jobs["log_rotation_cleanup"]["window_start"] == (5, 0)
    assert jobs["log_rotation_cleanup"]["window_end"] == (6, 50)


@pytest.mark.parametrize('trading,clock,marker,expected', [
    (False, (21, 5), 'START', 'skip_non_trading_day'),
    (True, (21, 5), 'START', 'in_progress'),
    (True, (22, 20), 'START', 'in_progress'),
    (True, (22, 35), 'START', 'fail'),
    (True, (21, 5), 'FAIL', 'fail'),
    (True, (21, 5), 'DONE', 'pass'),
    (True, (22, 35), 'OLD_DONE', 'fail'),
])
def test_dashboard_archive_calendar_eod_wait_and_terminal_failure(
    monkeypatch, tmp_path, trading, clock, marker, expected,
):
    import src.engine.error_detectors.cron_completion as cc

    day = '2026-10-08' if trading else '2026-10-09'
    log = tmp_path / 'logs/dashboard_db_archive_cron.log'
    log.parent.mkdir()
    marker_day = '2026-10-07' if marker == 'OLD_DONE' else day
    log.write_text(f'[{marker.removeprefix("OLD_")}] dashboard_db_archive target_date={marker_day}\n')
    monkeypatch.setattr(cc, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(cc, '_today_kst', lambda: day)
    monkeypatch.setattr(cc, '_kst_time_tuple', lambda: clock)
    monkeypatch.setattr(cc, 'is_krx_trading_day', lambda _: trading)
    monkeypatch.setattr(cc, 'CRON_JOB_REGISTRY', [dict(job) for job in CRON_JOB_REGISTRY
                                               if job['id'] == 'dashboard_db_archive'])
    monkeypatch.setattr(cc, 'load_installed_crontab', lambda: '50 20 * * 1-5 # DASHBOARD_DB_ARCHIVE_2050')
    result = CronCompletionDetector(dry_run=True).check()
    assert result.details['dashboard_db_archive_status'] == expected
    assert result.severity == ('fail' if expected == 'fail' else 'pass')


@pytest.mark.parametrize(
    ("finalized_at", "cleaned_at", "expected_status", "expected_severity"),
    [
        ("06:42:00", "06:45:00", "pass", "pass"),
        ("07:11:31", "08:28:17", "recovered_late", "warning"),
    ],
)
def test_morning_finalization_checks_previous_source_date_and_completion_time(
    monkeypatch, tmp_path, finalized_at, cleaned_at, expected_status, expected_severity
):
    import src.engine.automation.postclose_finalization_generation as generation
    import src.engine.error_detectors.cron_completion as cc

    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    (logs_dir / "postclose_finalization_cron.log").write_text(
        "[DONE] postclose_finalization target_date=2026-09-28 "
        f"finished_at=2026-09-29T{finalized_at}+0900 "
        f"chain_sha256={'a' * 64} snapshot_generation_sha256={'b' * 64} "
        f"detector_run_id=cron-abc detector_report_sha256={'c' * 64}\n"
    )
    (logs_dir / "log_rotation_cleanup_cron.log").write_text(
        "[DONE] log_rotation_cleanup target_date=2026-09-28 "
        f"finished_at=2026-09-29T{cleaned_at}+0900\n"
    )
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (12, 16))
    monkeypatch.setattr(
        cc, "CRON_JOB_REGISTRY",
        [
            dict(job)
            for job in CRON_JOB_REGISTRY
            if job["id"] in {"postclose_finalization", "log_rotation_cleanup"}
        ],
    )
    monkeypatch.setattr(
        cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500"
    )
    def marker_check(*args, validation_details):
        validation_details.update(basis='consumed_intraday_preserved_historical_generation',
                                  runtime_effect=False, new_finalization_claimed=False)
        return []
    monkeypatch.setattr(generation, "finalization_marker_issues", marker_check)

    result = CronCompletionDetector(dry_run=True).check()

    assert result.details["postclose_finalization_source_date"] == "2026-09-28"
    assert result.details["postclose_finalization_effective_date"] == "2026-09-29"
    assert result.details["postclose_finalization_status"] == expected_status
    assert result.details["log_rotation_cleanup_status"] == expected_status
    assert result.severity == expected_severity
    assert "no today marker" not in result.summary
    evidence = result.details['postclose_finalization_generation_validation']
    assert evidence['basis'] == 'consumed_intraday_preserved_historical_generation'
    assert evidence['new_finalization_claimed'] is False


def test_morning_finalization_for_current_source_date_is_due_next_trading_day(
    monkeypatch, tmp_path
):
    import src.engine.error_detectors.cron_completion as cc

    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (12, 16))
    monkeypatch.setattr(
        cc, "CRON_JOB_REGISTRY",
        [dict(job) for job in CRON_JOB_REGISTRY if job["id"] == "postclose_finalization"],
    )
    monkeypatch.setattr(
        cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500"
    )
    detector = CronCompletionDetector(dry_run=True)
    detector.postclose_source_date = "2026-09-29"

    result = detector.check()

    assert result.details["postclose_finalization_effective_date"] == "2026-09-30"
    assert result.details["postclose_finalization_status"] == "not_yet_due"
    assert result.severity == "pass"


def test_morning_cleanup_still_fails_when_previous_source_receipt_is_missing(
    monkeypatch, tmp_path
):
    import src.engine.error_detectors.cron_completion as cc

    log_path = tmp_path / "logs/log_rotation_cleanup_cron.log"
    log_path.parent.mkdir()
    log_path.write_text(
        "[DONE] log_rotation_cleanup target_date=2026-09-25 "
        "finished_at=2026-09-28T06:30:00+0900\n"
    )
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (12, 16))
    monkeypatch.setattr(
        cc, "CRON_JOB_REGISTRY",
        [dict(job) for job in CRON_JOB_REGISTRY if job["id"] == "log_rotation_cleanup"],
    )
    monkeypatch.setattr(
        cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500"
    )

    result = CronCompletionDetector(dry_run=True).check()

    assert result.details["log_rotation_cleanup_source_date"] == "2026-09-28"
    assert result.details["log_rotation_cleanup_status"] == "fail"
    assert result.severity == "fail"


@pytest.mark.parametrize(
    ("parent_markers", "cleanup_markers", "cleanup_status"),
    [
        ("[FAIL] postclose_finalization target_date=2026-10-01 reason=predecessor_terminal_failure\n", "", "blocked_by_finalization"),
        ("[FAIL] postclose_finalization target_date=2026-10-01 reason=predecessor_timeout\n", "", "blocked_by_finalization"),
        ("[FAIL] postclose_finalization target_date=2026-09-30 reason=predecessor_terminal_failure\n", "", "fail"),
        ("[FAIL] postclose_finalization target_date=2026-10-01 reason=cleanup_failed\n", "", "fail"),
        ("[FAIL] other_job target_date=2026-10-01 text=[FAIL] postclose_finalization reason=predecessor_terminal_failure\n", "", "fail"),
        ("[FAIL] postclose_finalization target_date=2026-10-01 reason=predecessor_terminal_failure\n[START] postclose_finalization target_date=2026-10-01\n", "", "fail"),
        ("[FAIL] postclose_finalization target_date=2026-10-01 reason=predecessor_terminal_failure\n", "[START] log_rotation_cleanup target_date=2026-10-01\n[FAIL] log_rotation_cleanup target_date=2026-10-01\n", "fail"),
    ],
)
def test_cleanup_dependency_preserves_parent_failure_and_cleanup_authority(
    monkeypatch, tmp_path, parent_markers, cleanup_markers, cleanup_status
):
    import src.engine.error_detectors.cron_completion as cc

    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "postclose_finalization_cron.log").write_text(parent_markers)
    (logs / "log_rotation_cleanup_cron.log").write_text(cleanup_markers)
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-10-02")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (7, 0))
    monkeypatch.setattr(cc, "CRON_JOB_REGISTRY", [
        dict(job) for job in CRON_JOB_REGISTRY
        if job["id"] in {"postclose_finalization", "log_rotation_cleanup"}
    ])
    monkeypatch.setattr(cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500")
    result = CronCompletionDetector(dry_run=True).check()
    assert result.details["log_rotation_cleanup_status"] == cleanup_status
    assert result.severity == "fail"  # Parent failure is never excused.
    if cleanup_status == "blocked_by_finalization":
        assert result.details["postclose_finalization_status"] == "fail"
        assert "log_rotation_cleanup: no today marker" not in result.summary
        assert result.details["log_rotation_cleanup_predecessor"]["source_date"] == "2026-10-01"


def test_cleanup_dependency_does_not_accept_a_changing_parent_generation(monkeypatch, tmp_path):
    import src.engine.error_detectors.cron_completion as cc

    logs = tmp_path / "logs"
    logs.mkdir()
    parent = logs / "postclose_finalization_cron.log"
    parent.write_text("[FAIL] postclose_finalization target_date=2026-10-01 reason=predecessor_terminal_failure\n")
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    original = cc.CronCompletionDetector._read_once_markers

    def read_and_change(path, day):
        result = original(path, day)
        if path == parent:
            with parent.open("a") as stream:
                stream.write("[START] postclose_finalization target_date=2026-10-01\n")
        return result

    monkeypatch.setattr(cc.CronCompletionDetector, "_read_once_markers", staticmethod(read_and_change))
    assert cc.CronCompletionDetector._cleanup_predecessor_failure(
        logs / "log_rotation_cleanup_cron.log", "2026-10-01"
    ) is None


def test_explicit_previous_source_date_keeps_morning_window_open(
    monkeypatch, tmp_path
):
    import src.engine.error_detectors.cron_completion as cc

    log_path = tmp_path / "logs/log_rotation_cleanup_cron.log"
    log_path.parent.mkdir()
    log_path.write_text("")
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-29")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (5, 10))
    monkeypatch.setattr(
        cc, "CRON_JOB_REGISTRY",
        [dict(job) for job in CRON_JOB_REGISTRY if job["id"] == "log_rotation_cleanup"],
    )
    monkeypatch.setattr(
        cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500"
    )
    detector = CronCompletionDetector(dry_run=True)
    detector.postclose_source_date = "2026-09-28"

    result = detector.check()

    assert result.details["log_rotation_cleanup_status"] == "warning"
    assert "no today marker yet" in result.summary


@pytest.mark.parametrize(
    ("source_date", "effective_date", "selected_at", "expected_status"),
    [
        ("2026-09-28", "2026-09-29", "2026-09-29T12:04:57+09:00", "historical_gap"),
        ("2026-09-28", "2026-09-29", "2026-09-29T06:00:00+09:00", "fail"),
        ("2026-09-29", "2026-09-30", "2026-09-30T12:04:57+09:00", "fail"),
    ],
)
def test_only_preselection_0928_unbound_generation_is_historical(
    monkeypatch, tmp_path, source_date, effective_date, selected_at, expected_status
):
    import src.engine.automation.postclose_finalization_generation as generation
    import src.engine.error_detectors.cron_completion as cc

    log_path = tmp_path / "logs/postclose_finalization_cron.log"
    log_path.parent.mkdir()
    log_path.write_text(
        f"[DONE] postclose_finalization target_date={source_date} "
        f"finished_at={effective_date}T07:11:31+0900\n"
    )
    selection_path = tmp_path / "data/runtime/runtime_release_selection.json"
    selection_path.parent.mkdir(parents=True)
    selection_path.write_text(json.dumps({"selected_at_kst": selected_at}))
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: effective_date)
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (12, 16))
    monkeypatch.setattr(
        cc, "CRON_JOB_REGISTRY",
        [dict(job) for job in CRON_JOB_REGISTRY if job["id"] == "postclose_finalization"],
    )
    monkeypatch.setattr(
        cc, "load_installed_crontab", lambda: "0 5 * * * # POSTCLOSE_FINALIZATION_0500"
    )
    monkeypatch.setattr(
        generation,
        "finalization_marker_issues",
        lambda *_, **kw: ["finalization_generation_unbound"],
    )

    result = CronCompletionDetector(dry_run=True).check()

    assert result.details["postclose_finalization_status"] == expected_status
    assert result.severity == ("warning" if expected_status == "historical_gap" else "fail")


def test_error_detector_cron_install_preserves_release_routed_finalization(tmp_path):
    root = Path(__file__).resolve().parents[2]
    (tmp_path / "data/runtime").mkdir(parents=True)
    state = tmp_path / "crontab.txt"
    finalizer = ("55 21 * * 1-5 bash /home/ubuntu/KORStockScan/deploy/"
                 "run_runtime_release.sh finalize $(TZ=Asia/Seoul date +\\%F) "
                 "# POSTCLOSE_FINALIZATION_2155")
    state.write_text(finalizer + "\n")
    stub = tmp_path / "crontab"
    stub.write_text('#!/bin/sh\nif [ "$1" = -l ]; then cat "$CRONTAB_STATE"; '
                    'else cp "$1" "$CRONTAB_STATE"; fi\n')
    stub.chmod(0o755)
    env = {**os.environ, "PATH": f"{tmp_path}:{os.environ['PATH']}",
           "CRONTAB_STATE": str(state), "PROJECT_DIR": str(tmp_path)}
    for _ in range(2):
        subprocess.run(["bash", str(root / "deploy/install_error_detection_cron.sh")],
                       env=env, check=True, capture_output=True, text=True)
        lines = state.read_text().splitlines()
        assert lines.count(finalizer) == 1
        assert sum("# ERROR_DETECTION_FULL" in line for line in lines) == 3
        assert sum(line.startswith("35 22 ") and "ERROR_DETECTION_FULL_ARCHIVE_TERMINAL" in line
                   for line in lines) == 1


@pytest.mark.parametrize(
    "case,expected",
    [("running", "in_progress"), ("done", "pass")]
    + [
        (case, "fail")
        for case in (
            "failed",
            "wrong_date",
            "invalid_json",
            "no_live_pid",
            "terminal_fail",
            "deadline",
            "past_source",
            "other_owner",
        )
    ],
)
def test_postclose_completion_shares_exact_bounded_running_gate(
    monkeypatch, tmp_path, case, expected
):
    import src.engine.error_detectors.cron_completion as cc
    from src.engine.error_detectors.artifact_freshness import ArtifactFreshnessDetector

    now = datetime(2026, 9, 10, 21, 50)
    if case == "deadline":
        now = datetime(2026, 9, 10, 23, 20)
    elif case == "past_source":
        now = datetime(2026, 9, 11, 0, 5)
    job = dict(
        next(j for j in cc.CRON_JOB_REGISTRY if j["id"] == "threshold_cycle_postclose")
    )
    job.update(log="postclose.log", status_artifact="status.json")
    if case == "other_owner":
        job["id"] = "other_owner"
    payload = {
        "schema_version": 1,
        "report_type": "threshold_cycle_postclose_status",
        "target_date": "2026-09-10",
        "status": "running",
        "reason": "started",
        "exit_code": 0,
        "runtime_effect": False,
        "started_at": "2026-09-10T20:10:04+09:00",
    }
    if case == "failed":
        payload.update(status="failed", exit_code=1)
    elif case == "done":
        payload.update(status="succeeded", reason="completed")
    elif case == "wrong_date":
        payload["target_date"] = "2026-09-09"
    (tmp_path / "status.json").write_text(
        "{" if case == "invalid_json" else json.dumps(payload)
    )
    markers = "[START] postclose target_date=2026-09-10\n"
    if case == "terminal_fail":
        markers += "[FAIL] postclose target_date=2026-09-10\n"
    (tmp_path / "postclose.log").write_text(markers)
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "CRON_JOB_REGISTRY", [job])
    monkeypatch.setattr(
        cc,
        "load_installed_crontab",
        lambda: "10 20 * * 1-5 THRESHOLD_CYCLE_POSTCLOSE=true bash deploy/run_threshold_cycle_postclose.sh",
    )
    monkeypatch.setattr(cc, "_today_kst", lambda: now.date().isoformat())
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (now.hour, now.minute))
    monkeypatch.setattr(cc, "_now_kst_ts", lambda: now.timestamp())

    def matching_process(config, *, target_date):
        assert config["process_patterns"] == ["run_threshold_cycle_postclose.sh"]
        assert target_date == "2026-09-10"
        return case != "no_live_pid"

    monkeypatch.setattr(
        ArtifactFreshnessDetector,
        "_has_matching_live_process",
        staticmethod(matching_process),
    )
    detector = cc.CronCompletionDetector(dry_run=True)
    detector.postclose_source_date = "2026-09-10"
    result = detector.check()
    assert result.details[f"{job['id']}_status"] == expected
    assert result.severity == ("warning" if expected == "in_progress" else expected)


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch):
    import src.engine.error_detectors.cron_completion as cc

    monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: True)


def test_recovery_uses_original_source_date_not_midnight_not_yet_due(
    monkeypatch, tmp_path
):
    import src.engine.error_detectors.cron_completion as cc

    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-10")
    monkeypatch.setattr(cc, "_kst_time_tuple", lambda: (0, 20))
    monkeypatch.setattr(
        cc,
        "CRON_JOB_REGISTRY",
        [
            {
                "id": "test_recovery",
                "log": "tail.log",
                "window_start": (21, 55),
                "window_end": (23, 20),
                "mode": "once",
                "critical": True,
            }
        ],
    )
    (tmp_path / "tail.log").write_text(
        "[DONE] test target_date=2026-09-09 finished_at=2026-09-10T00:19:00\n"
    )
    detector = cc.CronCompletionDetector(dry_run=True)
    detector.postclose_source_date = "2026-09-09"
    result = detector.check()
    assert result.details["test_recovery_status"] == "pass"
    (tmp_path / "tail.log").write_text("[DONE] test target_date=2026-09-10\n")
    assert detector.check().severity == "fail"


class TestCronCompletionDetector:
    @pytest.mark.parametrize(
        "line",
        [
            "[DONE] controller target_date=2026-09-07 finished_at=2026-09-08T00:27:44",
            "[FAIL] controller finished_at=2026-09-08T00:27:44 target_date=2026-09-07",
            "[2026-09-08 00:27:44] [START] controller target_date=2026-09-07",
        ],
    )
    def test_explicit_source_date_overrides_midnight_completion_timestamp(self, line):
        assert CronCompletionDetector._filter_today_lines(line, "2026-09-08") == ""
        assert CronCompletionDetector._filter_today_lines(line, "2026-09-07") == line

    def test_pass_when_log_not_yet_due(self):
        detector = CronCompletionDetector()
        with _mock_time(5, 0):
            result = detector.check()
        assert result.severity in ("pass", "warning", "fail")

    def test_pass_when_recent_log_has_done(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_ok.log"
            log_file.write_text(
                "[START] test job\n[DONE] test job completed successfully\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "DONE" in result

    def test_warning_when_log_has_errors(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = Path(tmpdir) / "test_error.log"
            log_file.write_text(
                "[START] test job\n[FAIL] error occurred\n[ERROR] something broke\n",
                encoding="utf-8",
            )
            detector = CronCompletionDetector()
            result = detector._read_tail(log_file, 100)
            assert "FAIL" in result
            assert "ERROR" in result

    def test_count_errors(self):
        text = "[START] begin\n[ERROR] first\n[FAIL] second\n[DONE] ok"
        detector = CronCompletionDetector()
        assert detector._count_errors(text) == 2

    def test_count_errors_no_match(self):
        detector = CronCompletionDetector()
        assert detector._count_errors("[DONE] all good") == 0

    def test_read_tail_nonexistent(self):
        detector = CronCompletionDetector()
        result = detector._read_tail(Path("/nonexistent/log.log"), 100)
        assert result == ""

    def test_read_tail_includes_rotated_numeric_logs(self, tmp_path):
        log_file = tmp_path / "threshold_cycle_postclose_cron.log"
        (tmp_path / "threshold_cycle_postclose_cron.log.1").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-22\n"
            "[DONE] threshold-cycle postclose target_date=2026-05-22\n",
            encoding="utf-8",
        )
        log_file.write_text("", encoding="utf-8")

        result = CronCompletionDetector._read_tail(log_file, 100)

        assert "target_date=2026-05-22" in result
        assert "[DONE] threshold-cycle postclose" in result

    def test_last_terminal_marker_fail_after_done(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-09\n[FAIL] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "error"

    def test_last_terminal_marker_done_after_fail(self):
        detector = CronCompletionDetector()
        lines = "[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        assert detector._last_terminal_marker(lines) == "done"

    def test_last_terminal_marker_none(self):
        detector = CronCompletionDetector()
        lines = "just noise\nno markers\n"
        assert detector._last_terminal_marker(lines) == "none"

    def test_filter_today_lines_excludes_other_dates(self):
        detector = CronCompletionDetector()
        lines = "[DONE] target_date=2026-05-08\n[FAIL] target_date=2026-05-09\n[DONE] target_date=2026-05-09\n"
        filtered = detector._filter_today_lines(lines, "2026-05-09")
        assert "2026-05-08" not in filtered
        assert "[FAIL]" in filtered
        assert filtered.count("[DONE]") == 1

    def test_terminal_error_immediate_job_fails_inside_open_window(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "postclose_finalization_cron.log").write_text(
            "[START] postclose_finalization target_date=2026-09-03\n"
            "[FAIL] postclose_finalization target_date=2026-09-03 reason=cleanup_failed\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-03")
        monkeypatch.setattr(cc, "CRON_INSTALL_MARKERS", {})
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "postclose_finalization",
                    "log": "logs/postclose_finalization_cron.log",
                    "window_start": (21, 55),
                    "window_end": (23, 55),
                    "mode": "once",
                    "critical": True,
                    "terminal_error_immediate": True,
                }
            ],
        )

        with _mock_time(22, 5):
            result = CronCompletionDetector().check()

        assert result.severity == "fail"
        assert result.details["postclose_finalization_status"] == "fail"
        assert "terminal failure marker observed" in result.summary

    def test_update_kospi_start_only_before_extended_window_end_is_not_fail(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "update_kospi.log").write_text(
            "[START] update_kospi target_date=2026-05-12 started_at=2026-05-12T20:05:03+0900\n",
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-12")

        with _mock_time(20, 16):
            result = CronCompletionDetector().check()

        assert (
            "update_kospi: no completion marker after window end" not in result.summary
        )

    def test_long_verbose_log_keeps_once_job_done_marker_visible(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 run_threshold_cycle_postclose.sh # THRESHOLD_CYCLE_POSTCLOSE")

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        noise = "\n".join(
            f'{{"row": {idx}, "payload": "verbose report output"}}'
            for idx in range(300)
        )
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "\n".join(
                [
                    "[START] threshold-cycle postclose target_date=2026-05-15 started_at=2026-05-15T20:10:01+0900",
                    noise,
                    "[DONE] threshold-cycle postclose target_date=2026-05-15 finished_at=2026-05-15T21:39:19+0900",
                    noise,
                ]
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-15")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_postclose",
                    "log": "logs/threshold_cycle_postclose_cron.log",
                    "window_start": (20, 10),
                    "window_end": (21, 40),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(21, 45):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_postclose_status"] == "pass"

    def test_rotated_once_job_done_marker_keeps_cron_status_pass(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 run_threshold_cycle_postclose.sh # THRESHOLD_CYCLE_POSTCLOSE")

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log.1").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-22 started_at=2026-05-22T20:10:01+0900\n"
            "[DONE] threshold-cycle postclose target_date=2026-05-22 finished_at=2026-05-22T21:22:41+0900\n",
            encoding="utf-8",
        )
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "", encoding="utf-8"
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-22")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_postclose",
                    "log": "logs/threshold_cycle_postclose_cron.log",
                    "window_start": (20, 10),
                    "window_end": (21, 40),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(23, 25):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_postclose_status"] == "pass"

    def test_threshold_postclose_status_artifact_can_complete_pending_done_marker(
        self, monkeypatch, tmp_path
    ):
        import json
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 run_threshold_cycle_postclose.sh # THRESHOLD_CYCLE_POSTCLOSE")

        logs_dir = tmp_path / "logs"
        status_dir = tmp_path / "data" / "report" / "threshold_cycle_postclose_status"
        logs_dir.mkdir(parents=True)
        status_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-26 started_at=2026-05-26T20:10:01+0900\n",
            encoding="utf-8",
        )
        (status_dir / "threshold_cycle_postclose_2026-05-26.status.json").write_text(
            json.dumps(
                {
                    "target_date": "2026-05-26",
                    "status": "succeeded",
                    "exit_code": 0,
                    "manual_recovery": {
                        "verification_status": "pass_with_pending_done_marker",
                    },
                }
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-26")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_postclose",
                    "log": "logs/threshold_cycle_postclose_cron.log",
                    "status_artifact": "data/report/threshold_cycle_postclose_status/threshold_cycle_postclose_{date}.status.json",
                    "window_start": (20, 10),
                    "window_end": (21, 40),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(23, 0):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_postclose_status"] == "pass"
        assert (
            result.details["threshold_cycle_postclose_status_artifact_terminal"]
            == "done"
        )

    def test_once_job_status_artifact_success_overrides_older_failed_log(
        self, monkeypatch, tmp_path
    ):
        import json
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 POSTCLOSE_DONE_CONTROLLER_ENABLED=true TUNING_MONITORING_POSTCLOSE_ENABLED=true")

        logs_dir = tmp_path / "logs"
        status_dir = tmp_path / "data" / "report" / "tuning_monitoring" / "status"
        logs_dir.mkdir(parents=True)
        status_dir.mkdir(parents=True)
        (logs_dir / "tuning_monitoring_postclose_cron.log").write_text(
            "\n".join(
                [
                    "[START] tuning_monitoring_postclose target_date=2026-05-26 started_at=2026-05-26T20:10:01+0900",
                    "[FAIL] tuning_monitoring_postclose target_date=2026-05-26 reason=threshold_cycle_postclose_not_done",
                    "[ERROR] tuning monitoring postclose failed status=1",
                ]
            ),
            encoding="utf-8",
        )
        (status_dir / "tuning_monitoring_postclose_2026-05-26.json").write_text(
            json.dumps(
                {"target_date": "2026-05-26", "status": "success", "exit_code": 0}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-26")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "tuning_monitoring_postclose",
                    "log": "logs/tuning_monitoring_postclose_cron.log",
                    "status_artifact": "data/report/tuning_monitoring/status/tuning_monitoring_postclose_{date}.json",
                    "window_start": (20, 10),
                    "window_end": (21, 55),
                    "mode": "once",
                    "critical": False,
                }
            ],
        )

        with _mock_time(23, 0):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["tuning_monitoring_postclose_status"] == "pass"
        assert (
            result.details["tuning_monitoring_postclose_status_artifact_terminal"]
            == "done"
        )

    def test_once_job_date_status_done_artifact_completes_missing_wrapper_marker(
        self, monkeypatch, tmp_path
    ):
        import json
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 POSTCLOSE_DONE_CONTROLLER_ENABLED=true TUNING_MONITORING_POSTCLOSE_ENABLED=true")

        logs_dir = tmp_path / "logs"
        status_dir = tmp_path / "data" / "report" / "postclose_done_controller"
        logs_dir.mkdir(parents=True)
        status_dir.mkdir(parents=True)
        (logs_dir / "postclose_done_controller_cron.log").write_text(
            "\n".join(
                [
                    "[START] postclose_done_controller target_date=2026-06-04 started_at=2026-06-04T20:40:01+0900",
                    '{"status": "blocked_recoverable_action_failed", "date": "2026-06-04"}',
                ]
            ),
            encoding="utf-8",
        )
        (status_dir / "postclose_done_controller_2026-06-04.json").write_text(
            json.dumps({"date": "2026-06-04", "status": "done"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-06-04")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "postclose_done_controller",
                    "log": "logs/postclose_done_controller_cron.log",
                    "status_artifact": "data/report/postclose_done_controller/postclose_done_controller_{date}.json",
                    "window_start": (20, 10),
                    "window_end": (21, 55),
                    "mode": "once",
                    "critical": True,
                }
            ],
        )

        with _mock_time(20, 45):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["postclose_done_controller_status"] == "pass"
        assert (
            result.details["postclose_done_controller_status_artifact_terminal"]
            == "done"
        )

    def test_once_job_failed_status_artifact_overrides_older_done_log(
        self, monkeypatch, tmp_path
    ):
        import json
        import src.engine.error_detectors.cron_completion as cc
        monkeypatch.setattr(cc, "load_installed_crontab", lambda: "10 20 * * 1-5 POSTCLOSE_DONE_CONTROLLER_ENABLED=true TUNING_MONITORING_POSTCLOSE_ENABLED=true")

        logs_dir = tmp_path / "logs"
        status_dir = tmp_path / "data" / "report" / "tuning_monitoring" / "status"
        logs_dir.mkdir(parents=True)
        status_dir.mkdir(parents=True)
        (logs_dir / "tuning_monitoring_postclose_cron.log").write_text(
            "[DONE] tuning_monitoring_postclose target_date=2026-05-26 finished_at=2026-05-26T21:45:00+0900\n",
            encoding="utf-8",
        )
        (status_dir / "tuning_monitoring_postclose_2026-05-26.json").write_text(
            json.dumps(
                {"target_date": "2026-05-26", "status": "failed", "exit_code": 1}
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-05-26")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "tuning_monitoring_postclose",
                    "log": "logs/tuning_monitoring_postclose_cron.log",
                    "status_artifact": "data/report/tuning_monitoring/status/tuning_monitoring_postclose_{date}.json",
                    "window_start": (20, 10),
                    "window_end": (21, 55),
                    "mode": "once",
                    "critical": False,
                }
            ],
        )

        with _mock_time(23, 0):
            result = CronCompletionDetector().check()

        assert result.severity == "fail"
        assert result.details["tuning_monitoring_postclose_status"] == "fail"
        assert (
            result.details["tuning_monitoring_postclose_status_artifact_terminal"]
            == "failed"
        )

    def test_trading_day_only_jobs_skip_on_non_trading_day(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: False)
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_preopen",
                    "log": "logs/threshold_cycle_preopen_cron.log",
                    "window_start": (7, 35),
                    "window_end": (7, 50),
                    "mode": "once",
                    "critical": True,
                    "trading_day_only": True,
                }
            ],
        )

        with _mock_time(10, 45):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert (
            result.details["threshold_cycle_preopen_status"] == "skip_non_trading_day"
        )

    def test_disabled_job_ids_skip_configured_cron_job(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: True)
        monkeypatch.setenv("KORSTOCKSCAN_DISABLED_CRON_JOBS", "final_ensemble_scanner")
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "final_ensemble_scanner",
                    "log": "logs/ensemble_scanner.log",
                    "window_start": (7, 20),
                    "window_end": (8, 0),
                    "mode": "once",
                    "critical": True,
                    "trading_day_only": True,
                }
            ],
        )

        with _mock_time(8, 10):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["final_ensemble_scanner_status"] == "disabled_by_env"

    def test_uninstalled_registered_job_is_terminally_disabled(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc

        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "_today_kst", lambda: "2026-08-05")
        monkeypatch.setattr(
            cc,
            "load_installed_crontab",
            lambda: "10 20 * * 1-5 runner # THRESHOLD_CYCLE_POSTCLOSE\n",
        )
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "swing_live_dry_run",
                    "log": "logs/swing_live_dry_run_cron.log",
                    "window_start": (0, 0),
                    "window_end": (0, 1),
                    "mode": "once",
                    "critical": False,
                    "trading_day_only": True,
                }
            ],
        )

        with _mock_time(21, 0):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["swing_live_dry_run_status"] == "disabled_not_installed"

    def test_skipped_status_artifact_is_terminal_success(self, tmp_path):
        today = "2026-08-05"
        status_path = tmp_path / "status.json"
        status_path.write_text(
            json.dumps({"target_date": today, "status": "skipped", "exit_code": 0}),
            encoding="utf-8",
        )

        state = CronCompletionDetector._status_artifact_terminal(
            {"status_artifact": str(status_path)}, today
        )

        assert state == "done"

    def test_once_job_can_pass_with_terminal_status_artifact_without_log_file(
        self, monkeypatch, tmp_path
    ):
        import src.engine.error_detectors.cron_completion as cc

        monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
        monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: True)
        today = cc._today_kst()
        status_dir = tmp_path / "data/report/threshold_cycle_preopen_status"
        status_dir.mkdir(parents=True)
        (status_dir / f"threshold_cycle_preopen_{today}.status.json").write_text(
            json.dumps({"status": "succeeded", "target_date": today}),
            encoding="utf-8",
        )
        monkeypatch.setattr(
            cc,
            "CRON_JOB_REGISTRY",
            [
                {
                    "id": "threshold_cycle_preopen",
                    "log": "logs/threshold_cycle_preopen_cron.log",
                    "status_artifact": "data/report/threshold_cycle_preopen_status/threshold_cycle_preopen_{date}.status.json",
                    "window_start": (7, 35),
                    "window_end": (7, 50),
                    "mode": "once",
                    "critical": True,
                    "trading_day_only": True,
                }
            ],
        )

        with _mock_time(8, 10):
            result = CronCompletionDetector().check()

        assert result.severity == "pass"
        assert result.details["threshold_cycle_preopen_status"] == "pass"
        assert (
            result.details["threshold_cycle_preopen_status_artifact_terminal"] == "done"
        )


@contextmanager
def _mock_time(hour: int, minute: int):
    import src.engine.error_detectors.cron_completion as cc

    class MockNow:
        def __init__(self):
            self.hour = hour
            self.minute = minute

    class MockDatetime:
        @staticmethod
        def now():
            return MockNow()

    orig = cc.datetime
    cc.datetime = MockDatetime
    try:
        yield
    finally:
        cc.datetime = orig


def test_once_markers_survive_verbose_output_and_new_run(tmp_path):
    path = tmp_path / "postclose.log"
    day = "2026-09-07"
    path.with_suffix(".log.1").write_text(
        f"[START] postclose target_date={day}\n[DONE] postclose target_date={day}\n"
    )
    path.write_text(f"[START] postclose target_date={day}\n" + "report row\n" * 6000)
    text = CronCompletionDetector._read_once_markers(path, day)
    assert "[START]" in text
    assert "[DONE]" not in text
    assert len(text.splitlines()) == 1
    with path.open("a") as stream:
        stream.write(f"[FAIL] postclose target_date={day}\n" + "report row\n" * 6000)
    assert (
        CronCompletionDetector._last_terminal_marker(
            CronCompletionDetector._read_once_markers(path, day)
        )
        == "error"
    )


def test_once_in_progress_marker_outside_tail_is_not_missing(monkeypatch, tmp_path):
    import src.engine.error_detectors.cron_completion as cc

    path = tmp_path / "postclose.log"
    path.write_text(
        "[START] postclose target_date=2026-09-07\n"
        + "status target_date=2026-09-07\n" * 6000
    )
    monkeypatch.setattr(cc, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(cc, "_today_kst", lambda: "2026-09-07")
    monkeypatch.setattr(
        cc,
        "CRON_JOB_REGISTRY",
        [
            dict(
                id="test_postclose",
                log="postclose.log",
                window_start=(20, 10),
                window_end=(21, 40),
                mode="once",
                critical=True,
            )
        ],
    )
    with _mock_time(21, 20):
        result = CronCompletionDetector().check()
    assert result.details["test_postclose_status"] == "in_progress"
    assert result.severity == "pass"
    with _mock_time(21, 45):
        result = CronCompletionDetector().check()
    assert result.details["test_postclose_status"] == "fail"


def test_once_marker_census_rejects_embedded_json_receipts(tmp_path):
    path = tmp_path / "postclose.log"
    path.write_text(
        "[START] postclose target_date=2026-09-07\n"
        '{"example": "[DONE] postclose target_date=2026-09-07"}\n'
    )
    text = CronCompletionDetector._read_once_markers(path, "2026-09-07")
    assert "[START]" in text
    assert "[DONE]" not in text


def test_self_audit_cannot_be_claimed_by_dead_or_unrelated_parent(monkeypatch):
    import os
    from src.engine.error_detectors import cron_completion as cc
    monkeypatch.setenv("POSTCLOSE_FINALIZATION_DETECTOR_DATE", "2026-09-17")
    monkeypatch.setenv("POSTCLOSE_FINALIZATION_DETECTOR_PARENT_PID", str(os.getpid()))
    assert cc._finalization_self_audit("2026-09-17") is False
    assert cc._finalization_self_audit("2026-09-18") is False
