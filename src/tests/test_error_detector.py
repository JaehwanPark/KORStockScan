from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detector import (
    ErrorDetectionEngine,
    OPERATIONAL_MUTATION_AUTHORITY,
    REPORT_SCHEMA_VERSION,
    REPORT_TYPE,
    validate_report_contract,
)
from src.engine.error_detectors.base import (
    BaseDetector,
    DetectionResult,
    register_detector,
    get_registered_detectors,
)


def test_artifact_checks_reuse_digests_between_invocations_but_run_semantics(
    monkeypatch, tmp_path
):
    import hashlib
    import src.engine.error_detector as module
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    data = tmp_path / "data"
    data.mkdir()
    source = data / "large-report.json"
    source.write_bytes(b"a" * (D.MIN_BYTES + 1))
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        D, "code_generation", lambda: {"code": "same-reviewed-generation"}
    )
    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.mode = "artifact_only"
    engine.postclose_source_date = None
    calls = []

    def check():
        calls.append(N._source_hash(str(source), N._signature(source)))
        return [
            DetectionResult(
                detector_id="artifact_freshness",
                category="artifact",
                severity="warning" if len(calls) == 3 else "pass",
                summary="fresh semantic check",
            )
        ]

    engine._run_all = check
    first = engine.run_all()[0]
    N._HASH_CACHE.clear()
    second = engine.run_all()[0]
    assert first.details["validation_io"]["full_reads"] == 1
    assert second.details["validation_io"]["full_reads"] == 0
    assert second.details["validation_io"]["reused_reads"] == 1
    source.write_bytes(b"b" * (D.MIN_BYTES + 1))
    third = engine.run_all()[0]
    assert third.severity == "warning"
    assert third.details["validation_io"]["full_reads"] == 1
    assert len(calls) == 3 and calls[0] == calls[1] != calls[2]


def test_observer_reuses_small_source_bytes_without_reusing_semantic_results(
    monkeypatch, tmp_path
):
    import hashlib
    import src.engine.error_detector as module
    from src.engine.infrastructure import validation_digest_session as D
    from src.engine.scalping import mechanistic_entry_runtime_policy as N

    data = tmp_path / "data"
    data.mkdir()
    sources = [tmp_path / "code.py", data / "first.json", data / "second.json"]
    for index, source in enumerate(sources):
        source.write_bytes(bytes([index]) * 128)
    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(D, "code_generation", lambda: {"code": "reviewed"})
    monkeypatch.setattr(N, "_HASH_MAX_ENTRIES", 2)
    N._hash_cache_clear()
    digested = []
    original = hashlib.file_digest

    def counted(stream, algorithm):
        if Path(stream.name) in sources:
            digested.append(Path(stream.name))
        return original(stream, algorithm)

    monkeypatch.setattr(hashlib, "file_digest", counted)
    semantic_calls = []
    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.mode = "artifact_only"
    engine.postclose_source_date = None

    def check():
        for _ in range(3):
            values = [N._source_hash(str(p), N._signature(p)) for p in sources]
            semantic_calls.append(values)
        return [DetectionResult("artifact_freshness", "artifact", "pass", "checked")]

    engine._run_all = check
    try:
        first = engine.run_all()[0]
        assert digested == sources
        assert len(semantic_calls) == 3
        assert first.details["validation_io"]["invocation_reused_reads"] == 6
        sources[1].write_bytes(b"changed")
        engine.run_all()
        assert digested == sources * 2
        assert len(semantic_calls) == 6
        assert semantic_calls[0][1] != semantic_calls[-1][1]
        assert all(
            not json.loads(p.read_text())["payload"]["entries"]
            for p in (data / "runtime/validation_digests/observer").glob("*.json")
        )
    finally:
        N._hash_cache_clear()


def test_digest_contention_defers_artifact_only_and_keeps_health_failure(
    monkeypatch, tmp_path
):
    from contextlib import contextmanager
    import src.engine.error_detector as module
    from src.engine.infrastructure import validation_digest_session as D

    monkeypatch.setattr(module, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(D, "code_generation", lambda: {"code": "same"})
    (tmp_path / "data").mkdir()

    @contextmanager
    def deferred(self):
        raise D.ValidationDeferred("validation_deferred:resource_wait")
        yield  # pragma: no cover

    monkeypatch.setattr(D.DigestSession, "activate", deferred)
    calls = []

    class Health:
        id, category = "process_health", "system"

        def check(self):
            calls.append(self.id)
            return DetectionResult(self.id, self.category, "fail", "Main missing")

    class Artifact:
        id, category = "artifact_freshness", "artifact"

        def check(self):
            pytest.fail("contended artifact validation was repeated")

    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.mode, engine.postclose_source_date = "full", None
    engine.initialization_failures = []
    engine.detectors = [Artifact(), Health()]
    artifact, health = engine.run_all()
    assert artifact.severity == "warning"
    assert artifact.details["observation_complete"] is False
    assert artifact.details["validation_status"] == "deferred"
    assert artifact.details["validation_io"]["full_reads"] == 0
    assert health.severity == "fail" and calls == ["process_health"]


class TestBaseDetector:
    def test_detection_result_defaults(self):
        result = DetectionResult(
            detector_id="test", category="test", severity="pass", summary="ok"
        )
        assert result.checked_at != ""
        assert result.recommended_action == ""

    def test_detection_result_post_init_sets_checked_at(self):
        result = DetectionResult(
            detector_id="test", category="test", severity="pass", summary="ok"
        )
        assert "T" in result.checked_at

    def test_register_detector_decorator(self):
        @register_detector
        class TestDetector(BaseDetector):
            id = "test_registration"
            name = "Test Detector"
            category = "test"

            def check(self):
                return DetectionResult(
                    detector_id=self.id,
                    category=self.category,
                    severity="pass",
                    summary="ok",
                )

        registered = get_registered_detectors()
        assert "test_registration" in registered

    def test_register_detector_requires_base(self):
        with pytest.raises(TypeError):

            @register_detector
            class NotADetector:
                id = "bad"

    def test_register_detector_requires_id(self):
        with pytest.raises(ValueError):

            @register_detector
            class NoIDDetector(BaseDetector):
                def check(self):
                    pass


class TestErrorDetectionEngine:
    def test_run_all_no_detectors(self):
        engine = ErrorDetectionEngine(dry_run=True)
        results = engine.run_all()
        assert isinstance(results, list)

    def test_summary_severity_pass(self):
        engine = ErrorDetectionEngine(dry_run=True)
        results = [
            DetectionResult(
                detector_id="a", category="test", severity="pass", summary="ok"
            ),
            DetectionResult(
                detector_id="b", category="test", severity="pass", summary="ok"
            ),
        ]
        assert engine.get_summary_severity(results) == "pass"

    def test_summary_severity_warning(self):
        engine = ErrorDetectionEngine(dry_run=True)
        results = [
            DetectionResult(
                detector_id="a", category="test", severity="pass", summary="ok"
            ),
            DetectionResult(
                detector_id="b", category="test", severity="warning", summary="warn"
            ),
        ]
        assert engine.get_summary_severity(results) == "warning"

    def test_summary_severity_fail(self):
        engine = ErrorDetectionEngine(dry_run=True)
        results = [
            DetectionResult(
                detector_id="a", category="test", severity="warning", summary="warn"
            ),
            DetectionResult(
                detector_id="b", category="test", severity="fail", summary="fail"
            ),
        ]
        assert engine.get_summary_severity(results) == "fail"

    def test_build_report_structure(self):
        engine = ErrorDetectionEngine(dry_run=True)
        results = [
            DetectionResult(
                detector_id="a", category="test", severity="pass", summary="ok"
            ),
        ]
        report = engine.build_report(results)
        assert "timestamp" in report
        assert report["schema_version"] == REPORT_SCHEMA_VERSION
        assert report["report_type"] == REPORT_TYPE
        assert report["mode"] == "full"
        assert report["runtime_effect"] is False
        assert report["runtime_mutation"] == "none"
        assert report["runtime_mutation_scope"] == "trading_strategy_runtime"
        assert report["operational_mutation_authority"] == list(
            OPERATIONAL_MUTATION_AUTHORITY
        )
        assert report["operational_mutations"] == []
        assert report["summary_severity"] == "pass"
        assert len(report["results"]) == 1
        assert report["results"][0]["detector_id"] == "a"

    def test_write_report_dry_run(self, tmp_path):
        engine = ErrorDetectionEngine(dry_run=True)
        results = [
            DetectionResult(
                detector_id="a", category="test", severity="pass", summary="ok"
            ),
        ]
        report = engine.build_report(results)
        engine.write_report(report)

    def test_write_report_creates_file(self, tmp_path):
        alt_report_dir = tmp_path / "error_detection"
        with patch("src.engine.error_detector.REPORT_DIR", alt_report_dir):
            engine = ErrorDetectionEngine(dry_run=False)
            results = [
                DetectionResult(
                    detector_id="a", category="test", severity="pass", summary="ok"
                ),
            ]
            report = engine.build_report(results)
            engine.write_report(report)
            report_file = (
                alt_report_dir
                / f"error_detection_{__import__('datetime').datetime.now().strftime('%Y-%m-%d')}.json"
            )
            assert report_file.exists()
            data = json.loads(report_file.read_text(encoding="utf-8"))
            assert data["summary_severity"] == "pass"
            assert not list(alt_report_dir.glob("*.tmp"))

    def test_write_report_supports_explicit_invocation_path(self, tmp_path):
        report_file = tmp_path / "invocation.json"
        engine = ErrorDetectionEngine(dry_run=False, mode="health_only")
        report = engine.build_report(engine.run_all())

        written = engine.write_report(report, report_file)

        assert written == report_file
        assert json.loads(report_file.read_text(encoding="utf-8"))["run_id"] == (
            engine.run_id
        )

    def test_initialization_failure_is_reported_not_silently_dropped(self):
        class BrokenDetector(BaseDetector):
            id = "broken_detector"
            name = "Broken"
            category = "test"

            def __init__(self, dry_run=False):
                raise RuntimeError("broken init")

            def check(self):  # pragma: no cover - construction must fail first
                raise AssertionError

        with (
            patch(
                "src.engine.error_detector.get_registered_detectors",
                return_value={"broken_detector": BrokenDetector},
            ),
            patch("src.engine.error_detector.REQUIRED_DETECTOR_IDS", frozenset()),
        ):
            engine = ErrorDetectionEngine(dry_run=True, mode="full", run_id="run-1")
            results = engine.run_all()
            report = engine.build_report(results)

        assert report["summary_severity"] == "fail"
        assert report["expected_detector_ids"] == ["broken_detector"]
        assert report["initialized_detector_count"] == 0
        assert report["initialization_failure_count"] == 1
        assert report["detector_count"] == 1
        assert report["results"][0]["details"]["stage"] == "initialization"

    def test_required_detector_missing_from_registry_is_reported(self):
        with patch(
            "src.engine.error_detector.get_registered_detectors", return_value={}
        ):
            engine = ErrorDetectionEngine(
                dry_run=True, mode="health_only", run_id="run-1"
            )
            report = engine.build_report(engine.run_all())

        assert report["summary_severity"] == "fail"
        assert report["expected_detector_ids"] == ["process_health"]
        assert report["initialization_failure_count"] == 1
        assert "not registered" in report["results"][0]["summary"]

    def test_unknown_mode_is_rejected(self):
        with pytest.raises(ValueError, match="Unsupported error detection mode"):
            ErrorDetectionEngine(dry_run=True, mode="unknown")

    def test_operational_mutations_are_separate_from_strategy_runtime(self):
        engine = ErrorDetectionEngine(dry_run=True, mode="health_only")
        results = [
            DetectionResult(
                detector_id="kiwoom_auth_8005_restart",
                category="runtime_auth",
                severity="warning",
                summary="restart requested",
                details={
                    "restart_requested": True,
                    "token_cache_invalidated": True,
                },
            ),
            DetectionResult(
                detector_id="stale_lock",
                category="process",
                severity="warning",
                summary="lock cleaned",
                details={"stale_locks_cleaned": ["a.lock"]},
            ),
        ]

        report = engine.build_report(results)

        assert report["runtime_mutation"] == "none"
        assert report["operational_mutations"] == [
            "kiwoom_auth_restart_flag",
            "kiwoom_token_cache_invalidation",
            "stale_lock_cleanup",
        ]
        assert report["operational_mutation_count"] == 3

    def test_validate_report_contract_rejects_stale_or_incomplete_provenance(self):
        engine = ErrorDetectionEngine(
            dry_run=True, mode="health_only", run_id="expected-run"
        )
        report = engine.build_report(engine.run_all())

        assert (
            validate_report_contract(
                report,
                expected_mode="health_only",
                expected_run_id="expected-run",
                expected_target_date=report["target_date"],
            )
            == []
        )

        report["run_id"] = "stale-run"
        report["detector_count"] += 1
        errors = validate_report_contract(
            report,
            expected_mode="health_only",
            expected_run_id="expected-run",
            expected_target_date=report["target_date"],
        )
        assert "run_id_mismatch" in errors
        assert "detector_count_mismatch" in errors

    def test_validate_report_contract_rejects_inconsistent_summary(self):
        engine = ErrorDetectionEngine(
            dry_run=True, mode="health_only", run_id="expected-run"
        )
        report = engine.build_report(engine.run_all())
        report["summary_severity"] = (
            "fail" if report["summary_severity"] != "fail" else "pass"
        )

        errors = validate_report_contract(
            report,
            expected_mode="health_only",
            expected_run_id="expected-run",
            expected_target_date=report["target_date"],
        )

        assert "summary_severity_mismatch" in errors


def test_error_detection_wrapper_validates_invocation_before_done():
    project_root = Path(__file__).resolve().parents[2]
    script = (project_root / "deploy" / "run_error_detection.sh").read_text(
        encoding="utf-8"
    )

    assert '--run-id "$RUN_ID"' in script
    assert '--report-file "$RUN_REPORT_FILE"' in script
    assert "validate_report_contract" in script
    assert '--report-file "$RUN_REPORT_FILE"' in script
    assert "report_validation_failed" in script
    assert script.index("validate_report_contract") < script.index(
        "[DONE] error detection"
    )


def test_error_detection_wrapper_publishes_valid_failed_recovery_receipt():
    project_root = Path(__file__).resolve().parents[2]
    script = (project_root / "deploy" / "run_error_detection.sh").read_text(
        encoding="utf-8"
    )

    # A recovery's failure severity is operational evidence, not a malformed
    # report. The canonical report must be replaced before the wrapper returns
    # non-zero to the finalization owner.
    assert 'errors.append("postclose_recovery_unresolved_failure")' not in script
    assert "postclose_recovery_unresolved_failure report_published=true" in script
    assert script.index("os.replace(tmp_path, canonical_path)") < script.index(
        "postclose_recovery_unresolved_failure report_published=true"
    )


def test_recovery_detector_active_lock_is_not_terminal_success(tmp_path):
    import fcntl
    import os
    import subprocess

    project_root = Path(__file__).resolve().parents[2]
    (tmp_path / "tmp").mkdir()
    lock_path = tmp_path / "tmp/run_error_detection.lock"
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = subprocess.run(
            [
                "bash",
                str(project_root / "deploy/run_error_detection.sh"),
                "full",
                "2026-09-09",
            ],
            env={**os.environ, "PROJECT_DIR": str(tmp_path)},
            capture_output=True,
            text=True,
            timeout=10,
        )
    assert result.returncode == 75
    assert "holds lock" in result.stdout
    assert "[DONE]" not in result.stdout


@pytest.mark.parametrize("release_lock,selection_rc", [(True, 43), (True, 75), (False, 43)])
def test_finalization_detector_waits_then_rechecks_selection(
    tmp_path, release_lock, selection_rc
):
    import fcntl
    import os
    import subprocess
    import time

    project_root = Path(__file__).resolve().parents[2]
    (tmp_path / "tmp").mkdir()
    python = tmp_path / ".venv/bin/python"
    python.parent.mkdir(parents=True)
    python.write_text(
        "#!/bin/bash\ncat >/dev/null\n"
        'echo rechecked > "$PROJECT_DIR/selection-checked"\n'
        f"exit {selection_rc}\n"
    )
    python.chmod(0o755)
    with (tmp_path / "tmp/run_error_detection.lock").open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        child = subprocess.Popen(
            ["bash", str(project_root / "deploy/run_error_detection.sh"),
             "full", "2026-10-26"],
            env={**os.environ, "PROJECT_DIR": str(tmp_path),
                 "ERROR_DETECTION_LOCK_WAIT_SEC": "1"},
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        try:
            time.sleep(0.15)
            assert child.poll() is None
            assert not (tmp_path / "selection-checked").exists()
            if release_lock:
                fcntl.flock(lock, fcntl.LOCK_UN)
            stdout, stderr = child.communicate(timeout=5)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate()
    assert child.returncode == (selection_rc if release_lock else 75), stderr
    assert (tmp_path / "selection-checked").exists() == release_lock
    assert "[DONE]" not in stdout
    assert not list((tmp_path / "tmp").glob("error_detection_*.json"))


@pytest.mark.parametrize("budget,source", [("-1", "2026-10-26"), ("NaN", "2026-10-26"), ("1", "")])
def test_detector_rejects_unbounded_or_unscoped_lock_wait(tmp_path, budget, source):
    import os
    import subprocess

    result = subprocess.run(
        ["bash", str(Path(__file__).resolve().parents[2] / "deploy/run_error_detection.sh"), "full", source],
        env={**os.environ, "PROJECT_DIR": str(tmp_path), "ERROR_DETECTION_LOCK_WAIT_SEC": budget},
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2
    assert "invalid_lock_wait_scope" in result.stdout
    assert not (tmp_path / "tmp").exists()


def test_postclose_recovery_retains_real_asof_and_disables_all_mutations(monkeypatch):
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import src.engine.error_detector as mod

    yesterday = (
        datetime.now(ZoneInfo("Asia/Seoul")).date() - timedelta(days=3)
    ).isoformat()

    class TestReadOnly(BaseDetector):
        category = "system"

        def check(self):
            assert self.dry_run is True
            return DetectionResult(self.id, self.category, "pass", "checked")

    registered = {
        key: type("ReadOnly" + key, (TestReadOnly,), {"id": key})
        for key in mod.REQUIRED_DETECTOR_IDS
    }
    monkeypatch.setattr(mod, "get_registered_detectors", lambda: registered)
    engine = ErrorDetectionEngine(
        postclose_source_date=yesterday, run_id="recovery-test"
    )
    report = engine.build_report(engine.run_all())
    assert report["target_date"] == yesterday
    assert (
        report["as_of_date"] == datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()
    )
    assert report["operational_mutation_authority"] == []
    assert report["operational_mutation_count"] == 0
    assert len(report["results"]) == 7
    kwargs = dict(
        expected_mode="full",
        expected_run_id="recovery-test",
        expected_target_date=yesterday,
    )
    assert validate_report_contract(report, **kwargs) == []
    report["operational_mutations"] = ["stale_lock_cleanup"]
    report["operational_mutation_count"] = 1
    assert (
        "postclose_recovery_operational_mutation_forbidden"
        in validate_report_contract(report, **kwargs)
    )
    report.pop("postclose_recovery")
    assert "timestamp_target_date_mismatch" in validate_report_contract(
        report, **kwargs
    )


def test_postclose_recovery_rejects_future_and_prebaseline_dates():
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()
    for delta in ((datetime(2026, 6, 4).date() - today).days, 1):
        with pytest.raises(ValueError):
            ErrorDetectionEngine(
                postclose_source_date=(today + timedelta(days=delta)).isoformat()
            )
    with pytest.raises(ValueError):
        ErrorDetectionEngine(
            mode="health_only", postclose_source_date=today.isoformat()
        )


def test_recovery_dispatcher_passes_scope_to_real_log_scanner(tmp_path, monkeypatch):
    import os
    import time
    from datetime import datetime, timedelta
    from zoneinfo import ZoneInfo
    import src.engine.error_detector as engine_module
    import src.engine.error_detectors.log_scanner as scanner_module

    class QuietDetector(BaseDetector):
        category = "system"

        def check(self):
            return DetectionResult(self.id, self.category, "pass", "checked")

    registered = {
        key: type("Quiet" + key, (QuietDetector,), {"id": key})
        for key in engine_module.REQUIRED_DETECTOR_IDS
    }
    registered["log_scanner"] = scanner_module.LogScanner
    monkeypatch.setattr(engine_module, "get_registered_detectors", lambda: registered)
    log = tmp_path / "owner_error.log"
    log.write_text("[ERROR] execution failed\n" * 1000)
    monkeypatch.setattr(scanner_module, "_get_error_log_files", lambda: [log])
    monkeypatch.setattr(scanner_module, "SCAN_STATE_PATH", tmp_path / "state.json")
    os.utime(log, (time.time() - 3 * 86400, time.time() - 3 * 86400))
    source = (
        datetime.now(ZoneInfo("Asia/Seoul")).date() - timedelta(days=3)
    ).isoformat()
    engine = ErrorDetectionEngine(postclose_source_date=source)
    result = next(r for r in engine.run_all() if r.detector_id == "log_scanner")
    assert result.severity == "warning"
    assert log.name in result.details["historical_unchanged_logs_not_current_burst"]
    assert result.details["postclose_source_date"] == source
    os.utime(log, None)
    result = next(r for r in engine.run_all() if r.detector_id == "log_scanner")
    assert result.severity == "fail"
    assert result.details["file_new_errors"][log.name] == 1000
    assert not scanner_module.SCAN_STATE_PATH.exists()


def test_daemon_alert_events_keep_health_fail_and_ignore_observation_clocks():
    from src.engine.error_detector import iter_daemon_alert_events

    state = {}
    results = [
        DetectionResult(
            "cron_completion",
            "cron",
            "fail",
            "terminal failure",
            {"postclose_finalization_source_date": "2026-10-01", "poll_clock": "first"},
        )
    ]
    assert [
        kind
        for kind, _ in iter_daemon_alert_events(
            results, state, target_date="2026-10-02"
        )
    ] == ["alert"]
    for clock in ["second", "third", "fourth"]:
        results[0].details["poll_clock"] = clock
        results[0].checked_at = clock
        assert (
            list(iter_daemon_alert_events(results, state, target_date="2026-10-02"))
            == []
        )
        assert results[0].severity == "fail"


def test_daemon_alert_events_realert_new_source_or_terminal_reason():
    from src.engine.error_detector import iter_daemon_alert_events

    state = {}
    r = DetectionResult(
        "cron_completion",
        "cron",
        "fail",
        "terminal failure",
        {
            "postclose_finalization_source_date": "2026-10-01",
            "log_rotation_cleanup_predecessor": {"reason": "first"},
        },
    )
    for source, reason in [
        ("2026-10-01", "first"),
        ("2026-10-02", "first"),
        ("2026-10-02", "second"),
    ]:
        r.details["postclose_finalization_source_date"] = source
        r.details["log_rotation_cleanup_predecessor"]["reason"] = reason
        assert [
            kind
            for kind, _ in iter_daemon_alert_events(
                [r], state, target_date="2026-10-02"
            )
        ] == ["alert"]


def test_daemon_alert_events_warning_is_not_recovery_and_recurrence_alerts():
    from src.engine.error_detector import iter_daemon_alert_events

    state = {}

    def events(severity):
        r = DetectionResult("cron_completion", "cron", severity, severity)
        return [
            kind
            for kind, _ in iter_daemon_alert_events(
                [r], state, target_date="2026-10-02"
            )
        ]

    assert events("fail") == ["alert"]
    assert events("warning") == []
    assert state
    assert events("pass") == ["recovered"]
    assert not state
    assert events("pass") == []
    assert events("fail") == ["alert"]


def test_daemon_alert_events_date_rollover_does_not_claim_historical_recovery():
    from src.engine.error_detector import iter_daemon_alert_events

    state = {}
    fail = DetectionResult("cron_completion", "cron", "fail", "terminal failure")
    assert [
        k for k, _ in iter_daemon_alert_events([fail], state, target_date="2026-10-02")
    ] == ["alert"]
    passed = DetectionResult("cron_completion", "cron", "pass", "ok")
    assert [
        k
        for k, _ in iter_daemon_alert_events([passed], state, target_date="2026-10-05")
    ] == ["current_date_pass"]
    assert fail.severity == "fail"
    assert [
        k for k, _ in iter_daemon_alert_events([fail], state, target_date="2026-10-05")
    ] == ["alert"]


def test_daemon_alert_events_auth_warning_escalation_and_failed_handler_retry():
    from src.engine.error_detector import iter_daemon_alert_events

    state = {}
    r = DetectionResult("kiwoom_auth_8005_restart", "auth", "warning", "pending")
    pending = iter_daemon_alert_events([r], state, target_date="2026-10-02")
    assert next(pending)[0] == "alert"
    pending.close()  # Consumer failed: it has not acknowledged the alert.
    assert not state
    assert [
        k for k, _ in iter_daemon_alert_events([r], state, target_date="2026-10-02")
    ] == ["alert"]
    assert list(iter_daemon_alert_events([r], state, target_date="2026-10-02")) == []
    r.severity = "fail"
    assert [
        k for k, _ in iter_daemon_alert_events([r], state, target_date="2026-10-02")
    ] == ["alert"]


def test_standalone_daemon_keeps_reporting_an_unresolved_incident(monkeypatch):
    from src.engine import error_detector as module

    reports, errors = [], []
    result = DetectionResult("cron_completion", "cron", "fail", "terminal failure")

    class FakeEngine:
        def __init__(self, **kwargs):
            pass

        def run_all(self):
            return [result]

        def build_report(self, results):
            return {"target_date": "2026-10-02", "severity": results[0].severity}

        def write_report(self, report):
            reports.append(report)

    def stop_after_four(_interval):
        if len(reports) == 4:
            raise KeyboardInterrupt

    monkeypatch.setattr(module, "ErrorDetectionEngine", FakeEngine)
    monkeypatch.setattr(module, "log_error", errors.append)
    monkeypatch.setattr(module, "log_info", lambda _message: None)
    monkeypatch.setattr(module.time, "sleep", stop_after_four)
    with pytest.raises(KeyboardInterrupt):
        module._daemon_loop(60, True)
    assert len(reports) == 4 and all(r["severity"] == "fail" for r in reports)
    assert errors == ["[ERROR_DETECTION] cron_completion: terminal failure"]


def test_sqlite_failure_preserves_database_phase_and_extended_code_without_downgrade(
    tmp_path,
):
    import sqlite3
    from src.engine.automation import main_trailing_source_store as store

    target = tmp_path / "missing.sqlite"

    class Broken(BaseDetector):
        id = "artifact_freshness"
        category = "artifact"

        def check(self):
            store._open_database(target, readonly=True, writer=False)

    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.initialization_failures = []
    engine.detectors = [Broken(dry_run=True)]
    engine.postclose_source_date = None
    result = engine._run_all()[0]
    assert result.severity == "fail"
    assert result.details["database"] == str(target)
    assert result.details["database_phase"] == "connect"
    assert result.details["sqlite_errorcode"] == sqlite3.SQLITE_CANTOPEN
    assert result.details["sqlite_errorname"] == "SQLITE_CANTOPEN"
    assert result.details["error_type"] == "OperationalError"


@pytest.mark.parametrize(
    "context", [None, "invalid", {"error": "hidden", "sqlite_errorcode": -1}]
)
def test_sqlite_diagnostic_context_cannot_hide_or_replace_original_failure(context):
    import sqlite3

    class Broken(BaseDetector):
        id = "artifact_freshness"
        category = "artifact"

        def check(self):
            error = sqlite3.OperationalError("original database failure")
            error.sqlite_context = context
            raise error

    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.initialization_failures = []
    engine.detectors = [Broken(dry_run=True)]
    engine.postclose_source_date = None
    result = engine._run_all()[0]
    assert result.severity == "fail"
    assert result.details["error"] == "original database failure"
    assert result.details["sqlite_errorcode"] is None


@pytest.fixture
def postclose_health():
    from src.engine.error_detector import REQUIRED_DETECTOR_IDS

    source, target = "2026-10-23", "2026-10-26"
    ids = sorted(REQUIRED_DETECTOR_IDS)
    report = dict(
        schema_version=REPORT_SCHEMA_VERSION,
        report_type=REPORT_TYPE,
        target_date=target,
        timestamp=target + "T08:00:00+09:00",
        mode="full",
        run_id="cron-completion-test",
        runtime_effect=False,
        runtime_mutation="none",
        runtime_mutation_scope="trading_strategy_runtime",
        operational_mutation_authority=list(OPERATIONAL_MUTATION_AUTHORITY),
        operational_mutations=[],
        operational_mutation_count=0,
        summary_severity="pass",
        expected_detector_count=len(ids),
        expected_detector_ids=ids,
        initialized_detector_count=len(ids),
        initialized_detector_ids=ids,
        initialization_failure_count=0,
        detector_count=len(ids),
        results=[
            dict(
                detector_id=name,
                severity="pass",
                summary="native contract pass",
                details={},
            )
            for name in ids
        ],
        startup_consumption=dict(
            status="ready",
            target_date=target,
            reason="current_pid_consumption_complete",
            pid=123,
            start_ticks="456",
            manifest_sha256="a" * 64,
            git_commit="b" * 40,
            release_root="/fixture/release",
        ),
        detector_code_provenance=dict(
            selected_release_consumed=True,
            selected_commit="b" * 40,
            selected_root="/fixture/release",
        ),
        startup_observer=dict(
            status="attempted",
            target_date=target,
            pid=123,
            producer_exit=0,
            observer_exit=0,
        ),
    )
    rows = {r["detector_id"]: r for r in report["results"]}
    rows["cron_completion"]["details"] = dict(
        postclose_finalization_source_date=source,
        postclose_finalization_status="pass",
    )
    rows["artifact_freshness"]["details"] = dict(
        completed_semantic_source=dict(
            status="receipt_selected",
            source_date=source,
            findings=[],
            generation="c" * 64,
        ),
        functional_semantic_coverage=dict(status="pass", findings=[]),
        semantic_alerts=[],
        semantic_observations=[
            dict(
                stage="postclose_handoff",
                semantics=dict(
                    status="done",
                    source_date=source,
                    bound_target_date=target,
                    findings=[],
                    report_sha256="c" * 64,
                ),
            )
        ],
        semantic_source_bindings=[
            dict(stage="postclose_handoff", source_date=source, generation="c" * 64)
        ],
    )
    for stage in (
        "initial_quantity",
        "main_stop_confirmation",
        "main_auxiliary_policy",
        "main_machine_policy",
    ):
        rows["artifact_freshness"]["details"]["semantic_observations"].append(
            dict(
                stage=stage,
                semantics=dict(
                    source_date=source, status="verified_carried", findings=[]
                ),
            )
        )
    return report, rows


def test_published_health_separates_cost_gap_from_successful_startup(
    postclose_health, tmp_path
):
    from copy import deepcopy

    report, rows = postclose_health
    details = rows["artifact_freshness"]["details"]
    details["semantic_alerts"] = [
        dict(
            stage="initial_quantity",
            source_date="2026-10-23",
            reason="initial_quantity_economic_source_gap",
            generation="d" * 64,
        )
    ]
    details["initial_quantity_semantics"] = dict(
        economic_sample_status="cost_eligible",
        eligible=33,
        total=37,
        excluded=[
            dict(record_id=49362, actual_cost=None),
            dict(record_id=49415, actual_cost=None),
        ],
        historical_record_ids=[49013, 49266],
    )
    rows["artifact_freshness"]["severity"] = report["summary_severity"] = "warning"
    original = deepcopy(report)
    engine = ErrorDetectionEngine.__new__(ErrorDetectionEngine)
    engine.dry_run = False
    path = engine.write_report(report, tmp_path / "health.json")
    published = json.loads(path.read_text())
    result = published.pop("postclose_completion")
    assert published == original  # Nulls, warnings and historical disposition survive.
    assert result["execution_status"] == result["startup_status"] == "complete"
    assert result["source_cost_semantic_status"] == "incomplete"
    assert result["overall_success"] is False
    assert result["current_findings"] == details["semantic_alerts"]


@pytest.mark.parametrize(
    "fault",
    [
        None,
        "cost_gap",
        "generation",
        "missing_coverage",
        "missing_alerts",
        "health_only",
        "missing_detector",
        "pending_self_audit",
        "startup_date",
        "startup_pid",
        "observer",
        "resource_warning",
        "missing_startup",
        "missing_quantity",
        "future_quantity",
        "filtered_finding",
        "release_mismatch",
        "malformed_coverage",
        "malformed_finding",
    ],
)
def test_completion_requires_independent_native_proofs(postclose_health, fault):
    from src.engine.error_detector import postclose_completion_assessment

    report, rows = postclose_health
    details = rows["artifact_freshness"]["details"]
    # Authenticated historical exclusions are already separated by the native
    # reader; age or an exclusion count is never interpreted here.
    details["historical_diagnostics"] = [dict(record_id=49013, actual_cost=None)]
    if fault == "cost_gap":
        details["semantic_alerts"] = [
            dict(reason="initial_quantity_economic_source_gap")
        ]
    elif fault == "generation":
        details["completed_semantic_source"]["generation"] = "e" * 64
    elif fault == "missing_coverage":
        details.pop("functional_semantic_coverage")
    elif fault == "missing_alerts":
        details.pop("semantic_alerts")
    elif fault == "health_only":
        report["mode"] = "health_only"
    elif fault == "missing_detector":
        report["results"].pop()
    elif fault == "pending_self_audit":
        rows["cron_completion"]["details"]["postclose_finalization_status"] = fault
    elif fault == "startup_date":
        report["startup_consumption"]["target_date"] = "2026-10-23"
    elif fault == "startup_pid":
        report["startup_consumption"]["pid"] = 0
    elif fault == "observer":
        report["startup_observer"]["observer_exit"] = 1
    elif fault == "resource_warning":
        rows["resource_usage"]["severity"] = report["summary_severity"] = "warning"
    elif fault == "missing_startup":
        report.pop("startup_consumption")
    elif fault == "missing_quantity":
        details["semantic_observations"].pop(1)
    elif fault == "future_quantity":
        details["semantic_observations"][1]["semantics"]["source_date"] = "2026-10-26"
    elif fault == "release_mismatch":
        report["detector_code_provenance"]["selected_commit"] = "f" * 40
    elif fault == "malformed_coverage":
        details["functional_semantic_coverage"] = ["pass"]
    elif fault == "malformed_finding":
        details["semantic_observations"][1]["semantics"]["findings"] = [{}]
    elif fault == "filtered_finding":
        details["semantic_observations"][1]["semantics"]["findings"] = [
            "new_cost_revision"
        ]
    result = postclose_completion_assessment(report)
    assert result["overall_success"] is (fault is None)
    assert result["runtime_effect"] is result["allowed_runtime_apply"] is False
    assert result["natural_acceptance_status"] == "not_assessed"
    assert details["historical_diagnostics"][0]["actual_cost"] is None
    if fault in {
        None,
        "pending_self_audit",
        "startup_date",
        "startup_pid",
        "observer",
        "resource_warning",
        "missing_startup",
    }:
        assert result["source_cost_semantic_status"] == "complete"


@pytest.mark.parametrize(
    "status,findings",
    [
        ("historical_diagnostic", ["initial_quantity_economic_source_gap"]),
        ("valid_empty", []),
        ("verified_carried", ["economics_null"]),
    ],
)
def test_completion_preserves_native_historical_null_and_valid_carry(
    postclose_health, status, findings
):
    from src.engine.error_detector import postclose_completion_assessment

    report, rows = postclose_health
    observation = rows["artifact_freshness"]["details"]["semantic_observations"][1][
        "semantics"
    ]
    observation.update(status=status, findings=findings, actual_cost=None)
    result = postclose_completion_assessment(report)
    assert result["source_cost_semantic_status"] == "complete"
    assert result["overall_success"] is True
    assert observation["actual_cost"] is None
