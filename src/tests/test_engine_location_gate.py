from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ENGINE_ROOT = ROOT / "src" / "engine"


LEGACY_ENGINE_ROOT_PY_FILES = {
    "__init__.py",
    "ai_engine_openai.py",
    "ai_prompt_contracts.py",
    "ai_response_contracts.py",
    "approval_contracts.py",
    "auto_promotion_contracts.py",
    "backfill_threshold_cycle_events.py",
    "bd_fbuy_accum_pre_scanner.py",
    "bedrock_nova_provider.py",
    "build_code_improvement_workorder.py",
    "build_codex_daily_workorder.py",
    "build_next_stage2_checklist.py",
    "build_tuning_monitoring_parquet.py",
    "buy_funnel_sentinel.py",
    "buy_pause_guard.py",
    "codebase_performance_workorder_report.py",
    "collect_remote_latency_baseline.py",
    "compare_tuning_shadow_diff.py",
    "compress_db_backfilled_files.py",
    "daily_report_service.py",
    "daily_threshold_cycle_report.py",
    "dashboard_data_repository.py",
    "error_detector.py",
    "error_detector_coverage.py",
    "fetch_remote_scalping_logs.py",
    "holding_exit_matrix_runtime.py",
    "holding_exit_observation_report.py",
    "holding_exit_sentinel.py",
    "institutional_flow_context.py",
    "ipo_listing_day_runner.py",
    "kiwoom_orders.py",
    "kiwoom_sniper_v2.py",
    "kiwoom_websocket.py",
    "latency_classifier_recommendation.py",
    "lifecycle_ai_context.py",
    "lifecycle_bucket_discovery.py",
    "lifecycle_decision_matrix.py",
    "lifecycle_decision_matrix_runtime.py",
    "log_archive_service.py",
    "macro_briefing_complete.py",
    "market_panic_breadth_collector.py",
    "ml_predictor.py",
    "monitor_snapshot_runtime.py",
    "notify_error_detection_admin.py",
    "notify_monitor_snapshot_admin.py",
    "notify_panic_state_transition.py",
    "observation_source_quality_audit.py",
    "ofi_ai_smoothing.py",
    "panic_buying_report.py",
    "panic_buying_state_detector.py",
    "panic_sell_defense_report.py",
    "panic_sell_state_detector.py",
    "pattern_lab_ai_review.py",
    "pattern_lab_currentness_audit.py",
    "pattern_lab_propagation_audit.py",
    "pipeline_event_summary.py",
    "pipeline_event_verbosity_report.py",
    "run_monitor_snapshot.py",
    "runtime_apply_bridge.py",
    "runtime_apply_gap_audit.py",
    "runtime_approval_summary.py",
    "scalp_entry_action_decision_matrix.py",
    "scalp_entry_adm_runtime.py",
    "scalp_sim_ai_deferred_review.py",
    "scalp_sim_ev_midcheck.py",
    "scalp_sim_overnight.py",
    "scalp_sim_scale_in_window_approval.py",
    "scalping_feature_packet.py",
    "scalping_pattern_lab_automation.py",
    "sentinel_event_cache.py",
    "server_report_comparison.py",
    "signal_radar.py",
    "sniper_analysis.py",
    "sniper_condition_handlers.py",
    "sniper_condition_handlers_big_bite.py",
    "sniper_config.py",
    "sniper_dynamic_thresholds.py",
    "sniper_entry_latency.py",
    "sniper_entry_metrics.py",
    "sniper_entry_pipeline_report.py",
    "sniper_entry_state.py",
    "sniper_execution_receipts.py",
    "sniper_gatekeeper_replay.py",
    "sniper_market_regime.py",
    "sniper_missed_entry_counterfactual.py",
    "sniper_overnight_gatekeeper.py",
    "sniper_performance_tuning_report.py",
    "sniper_position_tags.py",
    "sniper_post_sell_feedback.py",
    "sniper_s15_fast_track.py",
    "sniper_scale_in.py",
    "sniper_scale_in_utils.py",
    "sniper_state_handlers.py",
    "sniper_strength_momentum.py",
    "sniper_strength_observation_report.py",
    "sniper_strength_shadow_feedback.py",
    "sniper_sync.py",
    "sniper_time.py",
    "sniper_trade_review_report.py",
    "sniper_trade_utils.py",
    "split_entry_followup_audit.py",
    "strategy_position_performance_report.py",
    "swing_daily_simulation_report.py",
    "swing_lifecycle_audit.py",
    "swing_lifecycle_bucket_discovery.py",
    "swing_lifecycle_decision_matrix.py",
    "swing_pattern_lab_automation.py",
    "swing_sector_theme_source.py",
    "swing_selection_funnel_report.py",
    "swing_strategy_discovery_ev_report.py",
    "swing_strategy_discovery_label_builder.py",
    "swing_strategy_discovery_schema.py",
    "swing_strategy_discovery_sim.py",
    "sync_docs_backlog_to_project.py",
    "sync_github_project_calendar.py",
    "system_metric_sampler.py",
    "threshold_cycle_ev_report.py",
    "threshold_cycle_preopen_apply.py",
    "trade_pause_cli.py",
    "trade_pause_control.py",
    "trade_profit.py",
    "tuning_duckdb_repository.py",
    "verify_threshold_cycle_postclose_chain.py",
    "wait6579_ev_cohort_report.py",
}

ENGINE_ROOT_EXCEPTIONS_WITH_OWNERSHIP_REASONS = {
    # New exceptions are intentionally empty. If a future root-level module is
    # truly required, add it here with a concrete ownership reason instead of
    # expanding the legacy set.
}

ALLOWED_ENGINE_ROOT_PY_FILES = LEGACY_ENGINE_ROOT_PY_FILES | set(
    ENGINE_ROOT_EXCEPTIONS_WITH_OWNERSHIP_REASONS
)


def test_engine_root_python_modules_are_allowlisted():
    actual = {path.name for path in ENGINE_ROOT.glob("*.py")}

    unexpected = sorted(actual - ALLOWED_ENGINE_ROOT_PY_FILES)
    missing = sorted(ALLOWED_ENGINE_ROOT_PY_FILES - actual)

    assert unexpected == [], (
        "New src/engine root modules are blocked by the location gate. "
        "Place new code in a role package such as automation, swing, scalping, "
        "lifecycle, monitoring, risk, error_detectors, infrastructure, or ai. "
        "Only update this allowlist with a written ownership reason."
    )
    assert missing == [], "Engine-root allowlist contains files that no longer exist."


def test_engine_root_new_exceptions_require_written_ownership_reasons():
    invalid = {
        name: reason
        for name, reason in ENGINE_ROOT_EXCEPTIONS_WITH_OWNERSHIP_REASONS.items()
        if not isinstance(reason, str) or len(reason.strip()) < 40
    }

    assert invalid == {}, (
        "Each new src/engine root exception must include a concrete ownership "
        "reason. Prefer a role package unless the module is a stable root CLI "
        "or documented compatibility surface."
    )


def test_agents_documents_engine_root_location_gate():
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

    required_terms = (
        "`src/engine` root is closed to new Python modules by default",
        "engine-root allowlist test",
        "written ownership reason",
        "Prefer existing role packages",
        "Wrapper modules must be temporary compatibility surfaces",
    )
    missing = [term for term in required_terms if term not in text]

    assert missing == []
