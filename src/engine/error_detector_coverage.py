from __future__ import annotations

from typing import Any


REQUIRED_CRON_JOB_IDS: set[str] = {
    "final_ensemble_scanner",
    "threshold_cycle_preopen",
    "buy_funnel_sentinel",
    "holding_exit_sentinel",
    "panic_sell_defense",
    "panic_buying",
    "buy_pause_guard",
    "monitor_snapshot",
    "threshold_cycle_calibration_intraday",
    "swing_live_dry_run",
    "threshold_cycle_postclose",
    "swing_model_retrain_postclose",
    "tuning_monitoring_postclose",
    "update_kospi",
    "dashboard_db_archive",
    "log_rotation_cleanup",
    "system_metric_sampler",
    "error_detection_full",
}


REQUIRED_ARTIFACT_IDS: set[str] = {
    "pipeline_events",
    "threshold_events",
    "daily_recommendations_csv",
    "daily_recommendations_diag",
    "threshold_runtime_env",
    "threshold_apply_plan",
    "buy_funnel_sentinel_report",
    "holding_exit_sentinel_report",
    "panic_sell_defense_report",
    "market_panic_breadth_report",
    "panic_buying_report",
    "openai_ws_stability_report",
    "threshold_postclose_report",
    "code_improvement_workorder",
    "pipeline_event_verbosity_report",
    "observation_source_quality_audit_report",
    "codebase_performance_workorder_report",
    "system_metric_samples",
    "swing_selection_funnel_report",
    "swing_lifecycle_audit_report",
    "swing_threshold_ai_review_report",
    "swing_improvement_automation_report",
    "swing_runtime_approval_report",
    "scalping_pattern_lab_automation_report",
    "swing_pattern_lab_automation_report",
    "swing_live_dry_run_status",
    "swing_model_retrain_report",
    "swing_model_retrain_diagnosis",
    "swing_bull_period_ai_review",
    "swing_model_retrain_status",
    "swing_model_registry_current",
    "swing_daily_simulation_status",
    "swing_daily_simulation_report",
    "update_kospi_status",
}


REQUIRED_HEARTBEAT_COMPONENTS: set[str] = {
    "main_loop",
    "telegram",
    "crisis_monitor",
    "error_detection",
    "sniper_engine",
    "scalping_scanner",
}


DETECTOR_COVERAGE_EXEMPTIONS: dict[str, str] = {
    "install_*": "installer/one-off setup scripts are not recurring runtime programs",
    "manual_replay": "manual replay commands are covered by their generated artifacts or explicit operator review",
}


def validate_detector_coverage(
    cron_registry: list[dict[str, Any]],
    artifact_registry: list[dict[str, Any]],
    heartbeat_components: set[str] | None = None,
) -> dict[str, list[str]]:
    cron_ids = {str(item.get("id", "")) for item in cron_registry}
    artifact_ids = {str(item.get("id", "")) for item in artifact_registry}
    heartbeat_ids = set(heartbeat_components or REQUIRED_HEARTBEAT_COMPONENTS)

    return {
        "missing_cron_jobs": sorted(REQUIRED_CRON_JOB_IDS - cron_ids),
        "missing_artifacts": sorted(REQUIRED_ARTIFACT_IDS - artifact_ids),
        "missing_heartbeat_components": sorted(REQUIRED_HEARTBEAT_COMPONENTS - heartbeat_ids),
    }
