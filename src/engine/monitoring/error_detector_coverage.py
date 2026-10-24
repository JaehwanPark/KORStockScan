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
    # The old docs/code-improvement-workorders Markdown monitor was removed
    # with 2c3b7597a. The current runner JSON and performance workorder remain.
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
    "error_detection",
    "sniper_engine",
    "scalping_scanner",
}


DETECTOR_COVERAGE_EXEMPTIONS: dict[str, str] = {
    "install_*": "installer/one-off setup scripts are not recurring runtime programs",
    "manual_replay": "manual replay commands are covered by their generated artifacts or explicit operator review",
}

# Contract inventory in the existing coverage owner. These are bindings, not
# new jobs, extra trading gates, or claims of natural execution/delivery.
FEATURE_CONTRACTS = (
    (
        "C01",
        "kiwoom_websocket.py",
        "native_item_epoch_sequence",
        "monitoring/submission_bottleneck_monitor.py",
    ),
    (
        "C02",
        "kiwoom_sniper_v2.py",
        "watch_admission_and_probe",
        "monitoring/submission_bottleneck_monitor.py",
    ),
    (
        "C03",
        "scalping/reversal_cumulative_postclose.py",
        "machine_component",
        "scalping/reversal_policy_status.py",
    ),
    (
        "C04",
        "scalping/reversal_auxiliary_tuning.py",
        "auxiliary_component",
        "error_detectors/artifact_freshness.py",
    ),
    (
        "C05",
        "sniper_state_handlers.py",
        "native_async_disposition",
        "monitoring/submission_bottleneck_monitor.py",
    ),
    (
        "C06",
        "scalping/pre_submit_delay_observation.py",
        "anchor_quote_observation_and_submit_terminal",
        "monitoring/submission_bottleneck_monitor.py",
    ),
    (
        "C07",
        "scalping/reversal_cumulative_runtime.py",
        "registered_price_progress",
        "scalping/continuous_reversal_policy_v6.py",
    ),
    (
        "C08",
        "scalping/entry_split_order_plan.py",
        "entry_plan_capacity_legs",
        "scalping/entry_split_monitor_projection.py",
    ),
    (
        "C09",
        "sniper_execution_receipts.py",
        "partial_and_residual_terminal",
        "scalping/entry_cancel_wait_runtime.py",
    ),
    (
        "C10",
        "scalping/main_custody_checkpoint.py",
        "native_main_manual_owner",
        "sniper_state_handlers.py",
    ),
    (
        "C11",
        "scalping/trailing_mechanical_strength.py",
        "original_buy_signal_gap_set",
        "scalping/holding_profit_exit_semantics.py",
    ),
    (
        "C12",
        "sniper_execution_receipts.py",
        "sell_ack_position_fact",
        "holding_exit_sentinel.py",
    ),
    (
        "C13",
        "automation/main_stop_postclose.py",
        "stop_vote_source_pair",
        "error_detectors/artifact_freshness.py",
    ),
    (
        "C14",
        "lifecycle/broker_cost_reconciliation.py",
        "completed_valid_cost",
        "runtime_approval_summary.py",
    ),
    (
        "C15",
        "scalping/ai_decision_quality.py",
        "source_quality_label_population",
        "automation/postclose_summary_handoff.py",
    ),
    (
        "C16",
        "automation/main_trailing_partitioned_research.py",
        "whole_population_manifest",
        "runtime_approval_summary.py",
    ),
    (
        "C17",
        "monitoring/policy_generation_contract.py",
        "native_capability_fixture",
        "error_detectors/artifact_freshness.py",
    ),
    (
        "C18",
        "automation/main_market_weakness_research.py",
        "optional_native_calendar_attempt_cumulative",
        "error_detectors/artifact_freshness.py",
    ),
    (
        "C19",
        "automation/operator_policy_succession.py",
        "registration_parent_cas",
        "automation/runtime_policy_bootstrap.py",
    ),
    (
        "C20",
        "automation/postclose_summary_handoff.py",
        "sealed_stage_strict_controller",
        "automation/postclose_done_controller.py",
    ),
    (
        "C21",
        "automation/intraday_release_handoff.py",
        "prepared_selector_actual_pid",
        "automation/ordered_intraday_deploy.py",
    ),
    (
        "C22",
        "lifecycle/research_storage.py",
        "bounded_logical_source_generation",
        "error_detectors/resource_usage.py",
    ),
    (
        "C23",
        "monitoring/semantic_incident_contract.py",
        "incident_and_transport_receipt",
        "notify_error_detection_admin.py",
    ),
    (
        "C24",
        "monitoring/error_detector_coverage.py",
        "installed_expected_off_retired",
        "error_detectors/artifact_freshness.py",
    ),
    (
        "C25",
        "scalping/avg_down_rebound.py",
        "main_owned_rebound_observation",
        "sniper_state_handlers.py",
    ),
)


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


def validate_semantic_coverage(
    day,
    *,
    stages=None,
    alert_stages=None,
    hooks=None,
    active_alerts=(),
    owner_error=None,
):
    """Check functional bindings in existing registries without running jobs."""
    from src.engine.automation import postclose_summary_handoff as native
    from src.engine.error_detectors import artifact_freshness as artifacts
    from src.engine import notify_error_detection_admin as notifier
    from src.engine.monitoring import submission_bottleneck_monitor as submission
    from pathlib import Path

    stage_registry = native.STAGE_REGISTRY if stages is None else stages
    allowed = notifier.SEMANTIC_ALERT_STAGES if alert_stages is None else alert_stages
    functions = (
        {
            "main_machine_policy": artifacts._continuous_reversal_result_semantics,
            "main_auxiliary_policy": artifacts._auxiliary_result_semantics,
            "postclose_handoff": artifacts._postclose_handoff_semantics,
            "holding_profit_exit": artifacts._holding_profit_exit_semantics,
            "initial_quantity": artifacts._initial_quantity_semantics,
            "main_stop_confirmation": artifacts._main_stop_semantics,
            "submission_bottleneck_monitor": submission.machine_semantics,
            "main_market_weakness_research": artifacts._optional_weakness_semantics,
        }
        if hooks is None
        else hooks
    )
    findings, bindings = [], {}
    for stage, (_, outputs) in stage_registry.items():
        if stage not in native.STAGE_REGISTRY:
            findings.append(stage + ":unowned_stage")
            continue
        prerequisites = native.stage_prerequisites(stage, day)
        commands = native.stage_commands(stage, day, day)
        paths = native.stage_artifacts(Path("/report"), day, stage)
        if (
            not outputs
            or not commands
            or not paths
            or any(
                parent not in stage_registry or parent == stage
                for parent in prerequisites
            )
        ):
            findings.append(stage + ":producer_artifact_prerequisite_binding_invalid")
        bindings[stage] = dict(
            producer_commands=commands,
            artifacts={k: str(v) for k, v in paths.items()},
            prerequisites=list(prerequisites),
            native_validator="stage_receipt_issues",
            terminal_consumer="strict_controller_prepared",
            expected_disposition="installed_stage_or_explicit_off",
            notifier_expected=stage in {"main_machine_policy", "main_auxiliary_policy"},
        )
    for stage in (
        "main_machine_policy",
        "main_auxiliary_policy",
        "postclose_handoff",
        "holding_profit_exit",
        "initial_quantity",
        "main_stop_confirmation",
    ):
        if stage not in allowed:
            findings.append(stage + ":notifier_unbound")
    for stage in (
        "main_machine_policy",
        "main_auxiliary_policy",
        "postclose_handoff",
        "submission_bottleneck_monitor",
        "holding_profit_exit",
        "initial_quantity",
        "main_stop_confirmation",
    ):
        if not callable(functions.get(stage)):
            findings.append(stage + ":native_semantic_hook_unbound")
    for stage in native.STAGE_REGISTRY.keys() - stage_registry.keys():
        findings.append(stage + ":stage_unregistered")
    from src.engine.monitoring.semantic_incident_contract import (
        STAGE_HOOKS,
        RECOVERY_STATES,
        METRIC_CONTRACT,
    )

    for stage in allowed:
        if stage not in STAGE_HOOKS:
            findings.append(stage + ":recovery_unbound")
    for state in (
        "operator_initial_registered",
        "verified_carried",
        "published_policy",
        "valid_empty",
        "pending_terminal",
    ):
        if state not in RECOVERY_STATES:
            findings.append(state + ":native_state_recovery_unbound")
    if active_alerts and owner_error:
        findings.append("current_owner_lookup:" + owner_error)
    for alert in active_alerts:
        if alert.get("owner_status") == "unresolved":
            findings.append(
                str(alert.get("stage")) + ":actionable_current_owner_unresolved"
            )
    feature_bindings = {}
    engine = Path(__file__).resolve().parents[1]
    for identity, producer, receipt, consumer in FEATURE_CONTRACTS:
        if (
            identity in feature_bindings
            or not (engine / producer).is_file()
            or not (engine / consumer).is_file()
        ):
            findings.append(identity + ":feature_contract_binding_invalid")
        feature_bindings[identity] = dict(
            producer=producer,
            receipt=receipt,
            consumer=consumer,
            expectedness=(
                "installed_optional_only"
                if identity == "C18"
                else "native_active_scope_with_off_retired_exclusions"
            ),
            production_owner=producer,
            repair_owner="current_unique_open_only_when_actionable",
            notifier=(
                "main_market_weakness_research_notify_for_recommendations"
                if identity == "C18"
                else "existing_incident_owner"
            ),
            natural_acceptance="not_proven_by_static_coverage",
        )
    return dict(
        status="pass" if not findings else "source_invalid",
        findings=sorted(set(findings)),
        feature_contracts=feature_bindings,
        metric_contract=METRIC_CONTRACT,
        coverage_kind="static_contract_bindings_not_delivery_receipt",
        stages=bindings,
        native_stage_count=len(bindings),
        decision_authority="report_only",
        historical_main="audit_only",
        retired_widget="retired_not_expected",
        surviving_episode="retired_not_expected",
    )
