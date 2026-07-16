from __future__ import annotations

from src.engine.error_detector_coverage import (
    DETECTOR_COVERAGE_EXEMPTIONS,
    REQUIRED_ARTIFACT_IDS,
    REQUIRED_CRON_JOB_IDS,
    REQUIRED_HEARTBEAT_COMPONENTS,
    validate_detector_coverage,
)
from src.engine.error_detectors.artifact_freshness import ARTIFACT_REGISTRY
from src.engine.error_detectors.cron_completion import CRON_JOB_REGISTRY


def test_required_detector_coverage_registry_is_complete():
    gaps = validate_detector_coverage(CRON_JOB_REGISTRY, ARTIFACT_REGISTRY)
    assert gaps == {
        "missing_cron_jobs": [],
        "missing_artifacts": [],
        "missing_heartbeat_components": [],
    }


def test_new_operational_feature_must_declare_detector_coverage():
    assert "error_detection_full" in REQUIRED_CRON_JOB_IDS
    assert "system_metric_sampler" in REQUIRED_CRON_JOB_IDS
    assert "panic_sell_defense" in REQUIRED_CRON_JOB_IDS
    assert "bd_fbuy_accum_pre_intraday" in REQUIRED_CRON_JOB_IDS
    assert "scalp_sim_overnight_preclose" in REQUIRED_CRON_JOB_IDS
    assert "panic_sell_defense_report" in REQUIRED_ARTIFACT_IDS
    assert "bd_fbuy_accum_pre_artifact" in REQUIRED_ARTIFACT_IDS
    assert "market_panic_breadth_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_lifecycle_audit_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_improvement_automation_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_live_dry_run_status" in REQUIRED_ARTIFACT_IDS
    assert "postclose_done_controller" in REQUIRED_CRON_JOB_IDS
    assert "postclose_done_controller_report" in REQUIRED_ARTIFACT_IDS
    assert "codex_workorder_runner_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_daily_simulation_status" in REQUIRED_ARTIFACT_IDS
    assert "swing_daily_simulation_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_pattern_lab_automation_report" in REQUIRED_ARTIFACT_IDS
    assert "scalping_pattern_lab_automation_report" in REQUIRED_ARTIFACT_IDS
    assert "pattern_lab_currentness_audit_report" in REQUIRED_ARTIFACT_IDS
    assert "pattern_lab_propagation_audit_report" in REQUIRED_ARTIFACT_IDS
    assert "lifecycle_decision_matrix_report" in REQUIRED_ARTIFACT_IDS
    assert "pipeline_event_verbosity_report" in REQUIRED_ARTIFACT_IDS
    assert "observation_source_quality_audit_report" in REQUIRED_ARTIFACT_IDS
    assert "codebase_performance_workorder_report" in REQUIRED_ARTIFACT_IDS
    assert "swing_model_registry_current" in REQUIRED_ARTIFACT_IDS
    assert "update_kospi_status" in REQUIRED_ARTIFACT_IDS
    assert "main_loop" in REQUIRED_HEARTBEAT_COMPONENTS
    assert DETECTOR_COVERAGE_EXEMPTIONS["install_*"].startswith("installer/")


def test_threshold_postclose_report_has_startup_grace_for_long_postclose_chain():
    artifact = next(
        item for item in ARTIFACT_REGISTRY if item["id"] == "threshold_postclose_report"
    )

    assert artifact["one_shot"] is True
    assert artifact["critical"] is True
    assert artifact["window_start"] == (20, 10)
    assert artifact["window_grace_sec"] >= 1200
    assert (
        artifact["suppress_missing_while_cron_in_progress"]["id"]
        == "threshold_cycle_postclose"
    )


def test_codex_workorder_runner_artifact_requires_completed_status():
    artifact = next(
        item
        for item in ARTIFACT_REGISTRY
        if item["id"] == "codex_workorder_runner_report"
    )

    assert artifact["json_ok_values"] == ["completed", "dry_run_planned"]
