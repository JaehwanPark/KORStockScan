from __future__ import annotations

from typing import Any

REQUIRED_CRON_JOB_IDS: set[str] = {
    "final_ensemble_scanner",
    "threshold_cycle_preopen",
    "buy_funnel_sentinel",
    "bd_fbuy_accum_pre_intraday",
    "holding_exit_sentinel",
    "panic_sell_defense",
    "buy_pause_guard",
    "monitor_snapshot",
    "swing_live_dry_run",
    "threshold_cycle_postclose",
    "postclose_done_controller",
    "swing_model_retrain_postclose",
    "tuning_monitoring_postclose",
    "update_kospi",
    "dashboard_db_archive",
    "log_rotation_cleanup",
    "postclose_finalization",
    "system_metric_sampler",
    "error_detection_full",
}


REQUIRED_ARTIFACT_IDS: set[str] = {
    "pipeline_events",
    "threshold_events",
    "daily_recommendations_csv",
    "daily_recommendations_diag",
    "runtime_policy_bootstrap",
    "threshold_preopen_status",
    "threshold_postclose_status",
    "submission_bottleneck_monitor",
    "holding_exit_sentinel_premarket_report",
    "holding_exit_sentinel_aftermarket_report",
    "buy_funnel_sentinel_report",
    "bd_fbuy_accum_pre_artifact",
    "holding_exit_sentinel_report",
    "panic_sell_defense_report",
    "market_panic_breadth_report",
    "runtime_approval_summary_report",
    "postclose_done_controller_report",
    "codex_workorder_runner_report",
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
    "swing_pattern_lab_automation_report",
    "pattern_lab_currentness_audit_report",
    "pattern_lab_propagation_audit_report",
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
        "missing_heartbeat_components": sorted(
            REQUIRED_HEARTBEAT_COMPONENTS - heartbeat_ids
        ),
    }


def validate_semantic_coverage(day, *, stages=None, alert_stages=None, hooks=None):
    """Check functional bindings in existing registries without running jobs."""
    from src.engine.automation import postclose_summary_handoff as native
    from src.engine.error_detectors import artifact_freshness as artifacts
    from src.engine import notify_error_detection_admin as notifier
    from src.engine.monitoring import submission_bottleneck_monitor as submission
    from pathlib import Path
    stage_registry = native.STAGE_REGISTRY if stages is None else stages
    allowed = notifier.SEMANTIC_ALERT_STAGES if alert_stages is None else alert_stages
    functions = {
        'main_machine_policy': artifacts._continuous_reversal_result_semantics,
        'main_auxiliary_policy': artifacts._auxiliary_result_semantics,
        'postclose_handoff': artifacts._postclose_handoff_semantics,
        'submission_bottleneck_monitor': submission.machine_semantics,
    } if hooks is None else hooks
    findings, bindings = [], {}
    for stage, (_, outputs) in stage_registry.items():
        if stage not in native.STAGE_REGISTRY:
            findings.append(stage + ':unowned_stage')
            continue
        prerequisites = native.stage_prerequisites(stage, day)
        commands = native.stage_commands(stage, day, day)
        paths = native.stage_artifacts(Path('/report'), day, stage)
        if (not outputs or not commands or not paths
                or any(parent not in stage_registry or parent == stage for parent in prerequisites)):
            findings.append(stage + ':producer_artifact_prerequisite_binding_invalid')
        bindings[stage] = dict(producer_commands=commands, artifacts={k: str(v) for k, v in paths.items()},
            prerequisites=list(prerequisites), native_validator='stage_receipt_issues',
            terminal_consumer='strict_controller_prepared',
            expected_disposition='installed_stage_or_explicit_off',
            notifier_expected=stage in {'main_machine_policy', 'main_auxiliary_policy'})
    for stage in ('main_machine_policy', 'main_auxiliary_policy', 'postclose_handoff'):
        if stage not in allowed:
            findings.append(stage + ':notifier_unbound')
    for stage in ('main_machine_policy', 'main_auxiliary_policy', 'postclose_handoff',
                  'submission_bottleneck_monitor'):
        if not callable(functions.get(stage)):
            findings.append(stage + ':native_semantic_hook_unbound')
    for stage in native.STAGE_REGISTRY.keys() - stage_registry.keys():
        findings.append(stage + ':stage_unregistered')
    return dict(status='pass' if not findings else 'source_invalid', findings=sorted(findings),
                stages=bindings, native_stage_count=len(bindings), decision_authority='report_only',
                historical_main='audit_only', retired_widget='retired_not_expected',
                surviving_episode='retired_not_expected')
