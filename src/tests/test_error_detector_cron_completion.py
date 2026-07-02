from __future__ import annotations

import os
import tempfile
import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from src.engine.error_detectors.cron_completion import CronCompletionDetector


@pytest.fixture(autouse=True)
def _force_trading_day(monkeypatch):
    import src.engine.error_detectors.cron_completion as cc

    monkeypatch.setattr(cc, "is_krx_trading_day", lambda target: True)


class TestCronCompletionDetector:
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

    def test_update_kospi_start_only_before_extended_window_end_is_not_fail(self, monkeypatch, tmp_path):
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

        assert "update_kospi: no completion marker after window end" not in result.summary

    def test_long_verbose_log_keeps_once_job_done_marker_visible(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        noise = "\n".join(f'{{"row": {idx}, "payload": "verbose report output"}}' for idx in range(300))
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

    def test_rotated_once_job_done_marker_keeps_cron_status_pass(self, monkeypatch, tmp_path):
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        logs_dir.mkdir(parents=True)
        (logs_dir / "threshold_cycle_postclose_cron.log.1").write_text(
            "[START] threshold-cycle postclose target_date=2026-05-22 started_at=2026-05-22T20:10:01+0900\n"
            "[DONE] threshold-cycle postclose target_date=2026-05-22 finished_at=2026-05-22T21:22:41+0900\n",
            encoding="utf-8",
        )
        (logs_dir / "threshold_cycle_postclose_cron.log").write_text("", encoding="utf-8")
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

    def test_threshold_postclose_status_artifact_can_complete_pending_done_marker(self, monkeypatch, tmp_path):
        import json
        import src.engine.error_detectors.cron_completion as cc

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
        assert result.details["threshold_cycle_postclose_status_artifact_terminal"] == "done"

    def test_once_job_status_artifact_success_overrides_older_failed_log(self, monkeypatch, tmp_path):
        import json
        import src.engine.error_detectors.cron_completion as cc

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
            json.dumps({"target_date": "2026-05-26", "status": "success", "exit_code": 0}),
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
        assert result.details["tuning_monitoring_postclose_status_artifact_terminal"] == "done"

    def test_once_job_date_status_done_artifact_completes_missing_wrapper_marker(self, monkeypatch, tmp_path):
        import json
        import src.engine.error_detectors.cron_completion as cc

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
        assert result.details["postclose_done_controller_status_artifact_terminal"] == "done"

    def test_once_job_failed_status_artifact_overrides_older_done_log(self, monkeypatch, tmp_path):
        import json
        import src.engine.error_detectors.cron_completion as cc

        logs_dir = tmp_path / "logs"
        status_dir = tmp_path / "data" / "report" / "tuning_monitoring" / "status"
        logs_dir.mkdir(parents=True)
        status_dir.mkdir(parents=True)
        (logs_dir / "tuning_monitoring_postclose_cron.log").write_text(
            "[DONE] tuning_monitoring_postclose target_date=2026-05-26 finished_at=2026-05-26T21:45:00+0900\n",
            encoding="utf-8",
        )
        (status_dir / "tuning_monitoring_postclose_2026-05-26.json").write_text(
            json.dumps({"target_date": "2026-05-26", "status": "failed", "exit_code": 1}),
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
        assert result.details["tuning_monitoring_postclose_status_artifact_terminal"] == "failed"

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
        assert result.details["threshold_cycle_preopen_status"] == "skip_non_trading_day"

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

    def test_once_job_can_pass_with_terminal_status_artifact_without_log_file(self, monkeypatch, tmp_path):
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
        assert result.details["threshold_cycle_preopen_status_artifact_terminal"] == "done"


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
