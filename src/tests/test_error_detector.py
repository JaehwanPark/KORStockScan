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
