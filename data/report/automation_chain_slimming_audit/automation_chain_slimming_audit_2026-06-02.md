# Automation Chain Slimming Audit (2026-06-02)

## Summary

- profile: `standard`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- total_steps: `55`
- core_count: `9`
- change_triggered_candidates: `13`
- duplicate_refresh_candidates: `6`
- manual_or_weekly_candidates: `26`
- deprecated_candidates: `0`
- estimated_risk: `low`
- classification_group_counts: `{'core_daily': 9, 'change_triggered': 20, 'manual_or_weekly': 26, 'deprecated_candidate': 0}`

## Slimming Candidates

| candidate_id | producer | classification/group | recommended_mode | reason |
| --- | --- | --- | --- | --- |
| `slim_001` | `src.engine.sniper_post_sell_feedback` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_002` | `src.engine.scalp_entry_action_decision_matrix` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_003` | `src.engine.scalp_sim_overnight` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_004` | `src.engine.institutional_flow_context` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_005` | `src.engine.scalping.microstructure_reaction_context` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_006` | `src.engine.scalp_sim_scale_in_window_approval` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_007` | `src.engine.lifecycle_ai_context` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_008` | `src.engine.lifecycle_decision_matrix` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | same_module_reexecuted_in_wrapper |
| `slim_009` | `src.engine.lifecycle_ai_context` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | same_module_reexecuted_in_wrapper |
| `slim_010` | `src.engine.lifecycle_bucket_discovery` | `change_triggered_candidate`/change_triggered | `change_triggered` | rolling_or_mtd_full_recompute |
| `slim_011` | `src.engine.lifecycle_decision_matrix` | `change_triggered_candidate`/change_triggered | `change_triggered` | rolling_or_mtd_full_recompute |
| `slim_012` | `src.engine.lifecycle_bucket_discovery` | `change_triggered_candidate`/change_triggered | `change_triggered` | rolling_or_mtd_full_recompute |
| `slim_013` | `src.engine.latency_classifier_recommendation` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_014` | `src.engine.market_panic_breadth_collector` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_015` | `src.engine.panic_sell_defense_report` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_016` | `src.engine.panic_buying_report` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_017` | `src.engine.openai_ws_stability_report` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_018` | `src.engine.scalp_sim_ai_deferred_review` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_019` | `src.engine.swing_strategy_discovery_sim` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_020` | `src.engine.swing_strategy_discovery_sim` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | same_module_reexecuted_in_wrapper |
| `slim_021` | `src.engine.swing_strategy_discovery_label_builder` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_022` | `src.engine.swing_strategy_discovery_ev_report` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_023` | `src.engine.swing_lifecycle_decision_matrix` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_024` | `src.engine.swing_lifecycle_bucket_discovery` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_025` | `src.engine.swing_lifecycle_audit` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_026` | `src.engine.scalping_pattern_lab_automation` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_027` | `src.engine.swing_pattern_lab_automation` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_028` | `src.engine.pattern_lab_currentness_audit` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_029` | `src.engine.pattern_lab_ai_review` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_030` | `src.engine.pipeline_event_verbosity_report` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_031` | `src.engine.observation_source_quality_audit` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_032` | `src.engine.codebase_performance_workorder_report` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_033` | `src.engine.automation.time_window_regime_counterfactual` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_034` | `src.engine.automation.producer_gap_source_bundle` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_035` | `src.engine.automation.producer_gap_discovery` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_036` | `src.engine.automation.stage_hook_workorder_discovery` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_037` | `src.engine.automation.stage_hook_runtime_scaffold` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_038` | `src.engine.build_code_improvement_workorder` | `side_branch_candidate`/change_triggered | `change_triggered` | workorder_generation_can_run_outside_strategy_ev_refresh |
| `slim_039` | `src.engine.pattern_lab_propagation_audit` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_040` | `src.engine.runtime_apply_gap_audit` | `triggered_deep_review_candidate`/change_triggered | `change_triggered` | deep_audit_or_ai_review_should_trigger_on_drift_or_handoff_gap |
| `slim_041` | `src.engine.build_next_stage2_checklist` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_042` | `src.engine.verify_threshold_cycle_postclose_chain` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | interim_verifier_duplicates_final_verifier |
| `slim_043` | `src.engine.sync_docs_backlog_to_project` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_044` | `src.engine.automation.tuning_performance_control_tower` | `manual_or_weekly_candidate`/manual_or_weekly | `manual_or_weekly` | support_report_not_direct_apply_boundary |
| `slim_045` | `src.engine.threshold_cycle_ev_report` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | same_module_reexecuted_in_wrapper |
| `slim_046` | `src.engine.threshold_cycle_ev_report` | `duplicate_refresh_candidate`/change_triggered | `change_triggered` | same_module_reexecuted_in_wrapper |

## Must Keep Daily

| step_id | producer | reason |
| --- | --- | --- |
| `postclose:lifecycle_decision_matrix:1` | `src.engine.lifecycle_decision_matrix` | direct_apply_or_core_handoff_boundary |
| `postclose:runtime_apply_bridge:1` | `src.engine.runtime_apply_bridge` | direct_apply_or_core_handoff_boundary |
| `postclose:runtime_approval_summary:1` | `src.engine.runtime_approval_summary` | direct_apply_or_core_handoff_boundary |
| `postclose:verify_threshold_cycle_postclose_chain:2` | `src.engine.verify_threshold_cycle_postclose_chain` | final_fail_closed_postclose_verifier |
| `postclose:threshold_cycle_ev_report:1` | `src.engine.threshold_cycle_ev_report` | direct_apply_or_core_handoff_boundary |
| `preopen:threshold_cycle_preopen_apply:1` | `src.engine.threshold_cycle_preopen_apply` | direct_apply_or_core_handoff_boundary |

## Implementation Workorders

| workorder_id | reason | runtime_effect |
| --- | --- | --- |
| `automation_chain_reduce_duplicate_refresh_v1` | multiple same-day refresh/verifier calls detected | `False` |
| `automation_chain_trigger_lifecycle_windows_v1` | rolling/MTD lifecycle recompute can be gated by input drift or promotion day | `False` |
| `automation_chain_trigger_deep_audits_v1` | AI/deep audit reports can run on upstream drift, new candidate, or handoff miss | `False` |
| `automation_chain_decouple_workorder_branch_v1` | code-improvement intake can be separated from strategy EV refresh loop | `False` |
