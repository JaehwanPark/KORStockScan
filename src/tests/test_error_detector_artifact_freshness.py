from __future__ import annotations

import os
import time
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src.engine.error_detectors.artifact_freshness import (
    ArtifactFreshnessDetector,
    ARTIFACT_REGISTRY,
)


_TRADING_MOCK = "src.engine.error_detectors.artifact_freshness.is_krx_trading_day"


class TestArtifactFreshnessDetector:
    def test_classify_pass(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], [])
        assert severity == "pass"

    def test_classify_warning(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify([], ["stale file"])
        assert severity == "warning"

    def test_classify_fail(self):
        detector = ArtifactFreshnessDetector()
        severity, summary = detector._classify(["missing"], [])
        assert severity == "fail"

    def test_fresh_file_passes(self, tmp_path):
        log_file = tmp_path / "fresh.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_fresh",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity in ("pass", "warning", "fail")

    def test_missing_critical_file_fails(self):
        artifact = {
            "id": "test_missing",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"

    def test_window_not_yet_due(self):
        artifact = {
            "id": "test_future",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (23, 59),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            detail_key = "test_future_status"
            assert detail_key in result.details
            assert result.details[detail_key] == "not_yet_due"

    def test_window_startup_grace_suppresses_missing_critical_file(self):
        now = datetime.now()
        artifact = {
            "id": "test_startup_grace",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "window_grace_sec": 7200,
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_startup_grace_status") == "startup_grace"

    def test_missing_critical_artifact_warns_when_upstream_cron_in_progress(self, tmp_path):
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        cron_log = tmp_path / "postclose.log"
        cron_log.write_text(f"[START] threshold-cycle postclose target_date={today}\n", encoding="utf-8")
        artifact = {
            "id": "threshold_postclose_report",
            "path_template": str(tmp_path / "missing_threshold_ev.json"),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "suppress_missing_while_cron_in_progress": {
                "id": "threshold_cycle_postclose",
                "log": str(cron_log),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("threshold_postclose_report_status") == "warning"
            assert result.details.get("threshold_postclose_report_upstream_status") == "in_progress"

    def test_missing_critical_artifact_warns_after_window_when_upstream_cron_still_in_progress(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        cron_log = tmp_path / "postclose.log"
        cron_log.write_text(f"[START] threshold-cycle postclose target_date={today}\n", encoding="utf-8")
        artifact = {
            "id": "threshold_postclose_report",
            "path_template": str(tmp_path / "missing_threshold_ev.json"),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
            "allow_missing_after_window_while_cron_in_progress": True,
            "suppress_missing_while_cron_in_progress": {
                "id": "threshold_cycle_postclose",
                "log": str(cron_log),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("threshold_postclose_report_status") == "warning"
            assert result.details.get("threshold_postclose_report_upstream_status") == "in_progress_after_window"

    def test_non_trading_day_skips(self):
        artifact = {
            "id": "test_skip",
            "path_template": "/nonexistent/path/file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "trading_day_only": True,
        }
        with (
            patch(_TRADING_MOCK, return_value=False),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_skip_status") == "skip_non_trading_day"

    def test_past_window_end_exists_passes(self, tmp_path):
        log_file = tmp_path / "past_window.log"
        log_file.write_text("content", encoding="utf-8")
        artifact = {
            "id": "test_past_window",
            "path_template": str(log_file),
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.details.get("test_past_window_status") == "pass_after_window"

    def test_window_end_boundary_existing_artifact_passes_after_window(self, tmp_path):
        log_file = tmp_path / "window_end_boundary.log"
        log_file.write_text("content", encoding="utf-8")
        stale_ts = time.time() - 901
        os.utime(log_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "test_window_end_boundary",
            "path_template": str(log_file),
            "max_staleness_sec": 900,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (now.hour, now.minute),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("test_window_end_boundary_status") == "pass_after_window"

    def test_one_shot_artifact_exists_passes_even_when_stale_inside_window(self, tmp_path):
        report_file = tmp_path / "threshold_cycle_ev.json"
        report_file.write_text("{}", encoding="utf-8")
        stale_ts = time.time() - 7200
        os.utime(report_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "threshold_postclose_report",
            "path_template": str(report_file),
            "max_staleness_sec": 1800,
            "critical": True,
            "one_shot": True,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("threshold_postclose_report_status") == "pass_one_shot"
            assert result.details.get("threshold_postclose_report_age_sec", 0) > 1800

    def test_daily_recommendations_csv_content_date_suppresses_mtime_stale_inside_window(self, tmp_path):
        reco_file = tmp_path / "daily_recommendations_v2.csv"
        content_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        reco_file.write_text(
            "date,code,name,generated_at\n"
            f"{content_date},005930,삼성전자,{datetime.now().isoformat()}\n",
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(reco_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_csv",
            "path_template": str(reco_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "csv",
                "date_field": "date",
                "max_age_days": 7,
                "min_rows": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("daily_recommendations_csv_status") == "pass_content_date"
            assert result.details.get("daily_recommendations_csv_content_status") == "pass"
            assert result.details.get("daily_recommendations_csv_content_age_days") == 1

    def test_daily_recommendations_diag_content_date_suppresses_mtime_stale_inside_window(self, tmp_path):
        diag_file = tmp_path / "daily_recommendations_v2_diagnostics.json"
        content_date = (datetime.now() - timedelta(days=1)).date().isoformat()
        diag_file.write_text(
            f'{{"latest_date": "{content_date}", "selected_count": 3}}',
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(diag_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_diag",
            "path_template": str(diag_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "json",
                "date_field": "latest_date",
                "max_age_days": 7,
                "min_count_field": "selected_count",
                "min_count": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details.get("daily_recommendations_diag_status") == "pass_content_date"
            assert result.details.get("daily_recommendations_diag_content_status") == "pass"
            assert result.details.get("daily_recommendations_diag_selected_count") == 3

    def test_daily_recommendations_diag_content_date_stale_warns_inside_window(self, tmp_path):
        diag_file = tmp_path / "daily_recommendations_v2_diagnostics.json"
        content_date = (datetime.now() - timedelta(days=9)).date().isoformat()
        diag_file.write_text(
            f'{{"latest_date": "{content_date}", "selected_count": 3}}',
            encoding="utf-8",
        )
        stale_ts = time.time() - 7200
        os.utime(diag_file, (stale_ts, stale_ts))
        now = datetime.now()
        artifact = {
            "id": "daily_recommendations_diag",
            "path_template": str(diag_file),
            "max_staleness_sec": 3600,
            "critical": False,
            "window_start": (now.hour, now.minute),
            "window_end": (23, 59),
            "content_freshness": {
                "format": "json",
                "date_field": "latest_date",
                "max_age_days": 7,
                "min_count_field": "selected_count",
                "min_count": 1,
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details.get("daily_recommendations_diag_status") == "warning"
            assert result.details.get("daily_recommendations_diag_content_status") == "stale_date"

    def test_past_window_end_missing_fails(self):
        artifact = {
            "id": "test_past_window_missing",
            "path_template": "/nonexistent/after_window_file.json",
            "max_staleness_sec": 600,
            "critical": True,
            "window_start": (0, 0),
            "window_end": (0, 1),
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "fail"

    def test_json_status_value_is_validated(self, tmp_path):
        status_file = tmp_path / "status.json"
        status_file.write_text('{"status": "failed"}', encoding="utf-8")
        artifact = {
            "id": "test_status_json",
            "path_template": str(status_file),
            "max_staleness_sec": 600,
            "critical": False,
            "json_status_field": "status",
            "json_ok_values": ["completed"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details["test_status_json_content_status"] == "failed"

    def test_json_status_ok_passes(self, tmp_path):
        status_file = tmp_path / "status.json"
        status_file.write_text('{"status": "completed"}', encoding="utf-8")
        artifact = {
            "id": "test_status_json",
            "path_template": str(status_file),
            "max_staleness_sec": 600,
            "critical": False,
            "json_status_field": "status",
            "json_ok_values": ["completed"],
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details["test_status_json_content_status"] == "completed"

    def test_swing_automation_artifacts_are_registered_with_status_guards(self):
        registry = {str(item["id"]): item for item in ARTIFACT_REGISTRY}

        assert registry["swing_live_dry_run_status"]["json_status_field"] == "status"
        assert "succeeded" in registry["swing_live_dry_run_status"]["json_ok_values"]
        assert registry["swing_live_dry_run_status"]["window_start"] == (15, 45)
        assert registry["swing_lifecycle_audit_report"]["window_start"] == (16, 10)
        assert registry["swing_runtime_approval_report"]["window_start"] == (16, 10)
        assert registry["swing_daily_simulation_status"]["json_status_field"] == "status"
        assert "swing_daily_simulation_{date}.json" in registry["swing_daily_simulation_report"]["path_template"]
        assert "swing_pattern_lab_automation_{date}.json" in registry["swing_pattern_lab_automation_report"]["path_template"]
        assert "current.json" in registry["swing_model_registry_current"]["path_template"]
        assert registry["pipeline_events"]["window_grace_sec"] == 300
        assert registry["threshold_events"]["critical"] is False
        assert registry["threshold_events"]["window_grace_sec"] == 300
        assert "partitioned_compact" in registry["threshold_events"]
        assert registry["threshold_postclose_report"]["one_shot"] is True

    def test_partitioned_threshold_events_checkpoint_passes_when_legacy_file_missing(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        checkpoint = tmp_path / "checkpoints" / f"{today}.json"
        part = tmp_path / f"date={today}" / "family=soft_stop_whipsaw_confirmation" / "part-000001.jsonl"
        checkpoint.parent.mkdir(parents=True)
        part.parent.mkdir(parents=True)
        checkpoint.write_text(
            '{"completed": true, "status": "completed", "written_count": 1}',
            encoding="utf-8",
        )
        part.write_text('{"stage":"soft_stop_micro_grace"}\n', encoding="utf-8")
        artifact = {
            "id": "threshold_events",
            "path_template": str(tmp_path / f"threshold_events_{today}.jsonl"),
            "max_staleness_sec": 600,
            "critical": False,
            "partitioned_compact": {
                "checkpoint_template": str(checkpoint),
                "partition_glob_template": str(tmp_path / f"date={today}" / "family=*" / "part-*.jsonl"),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "pass"
            assert result.details["threshold_events_status"] == "pass_partitioned_checkpoint"
            assert result.details["threshold_events_legacy_path_missing"] is True
            assert result.details["threshold_events_partitioned_completed"] is True
            assert result.details["threshold_events_partitioned_part_count"] == 1

    def test_partitioned_threshold_events_incomplete_checkpoint_warns(self, tmp_path):
        today = datetime.now().strftime("%Y-%m-%d")
        checkpoint = tmp_path / "checkpoints" / f"{today}.json"
        part = tmp_path / f"date={today}" / "family=soft_stop_whipsaw_confirmation" / "part-000001.jsonl"
        checkpoint.parent.mkdir(parents=True)
        part.parent.mkdir(parents=True)
        checkpoint.write_text(
            '{"completed": false, "status": "paused_by_availability_guard", "paused_reason": "cpu_busy_pct>=95"}',
            encoding="utf-8",
        )
        part.write_text('{"stage":"soft_stop_micro_grace"}\n', encoding="utf-8")
        artifact = {
            "id": "threshold_events",
            "path_template": str(tmp_path / f"threshold_events_{today}.jsonl"),
            "max_staleness_sec": 600,
            "critical": False,
            "partitioned_compact": {
                "checkpoint_template": str(checkpoint),
                "partition_glob_template": str(tmp_path / f"date={today}" / "family=*" / "part-*.jsonl"),
            },
        }
        with (
            patch(_TRADING_MOCK, return_value=True),
            patch("src.engine.error_detectors.artifact_freshness.ARTIFACT_REGISTRY", [artifact]),
        ):
            detector = ArtifactFreshnessDetector()
            result = detector.check()
            assert result.severity == "warning"
            assert result.details["threshold_events_status"] == "warning"
            assert result.details["threshold_events_partitioned_completed"] is False
            assert result.details["threshold_events_partitioned_paused_reason"] == "cpu_busy_pct>=95"
