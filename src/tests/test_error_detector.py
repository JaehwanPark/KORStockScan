from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detector import ErrorDetectionEngine, REPORT_DIR
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
