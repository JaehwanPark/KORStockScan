# Threshold Cycle Postclose Verification - 2026-07-22

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-07-22 max_iterations=80 started_at=2026-07-22T20:10:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-07-22 ai_correction_provider=openai panic_sell_defense=true panic_buying=true market_panic_breadth=true scalp_sim_ai_deferred_review=true pipeline_event_verbosity=true quote_consistency_report=true intraday_ws_freshness_monitor=true observation_source_quality_audit=true ai_watching_score_smoothing_diagnostic=true codebase_performance_workorder=true pattern_lab_currentness_audit=true pattern_lab_ai_review=true time_window_regime_counterfactual=true producer_gap_discovery=true stage_hook_workorder_discovery=true stage_hook_runtime_scaffold=true pattern_lab_propagation_audit=true scalp_sim_overnight=true scalp_entry_adm=true entry_split_order_plan=true scale_in_split_order_plan=true entry_ai_gate_backtest=true tight_stop_entry_companion_report=true ai_score_optimization_backtest=true rising_missed_intraday_feedback_postclose=true rising_missed_scout_workorder=true rising_missed_normal_buy_bridge_candidate_discovery=true rising_missed_first_touch_calibration=true scalping_pyramid_intraday_feedback_postclose=true scalping_pyramid_quality_calibration=true scalping_avg_down_recovery_calibration=true rising_missed_classifier_prior=true one_share_threshold_opportunity=true one_share_threshold_opportunity_ai_provider=openai institutional_flow_context=true microstructure_reaction_context=true lifecycle_decision_matrix=true lifecycle_ai_context=true ldm_hypothesis_parent_refinement=true lifecycle_bucket_discovery=true lifecycle_bucket_windows=true lifecycle_bucket_window_list=rolling5d,rolling10d,mtd lifecycle_bucket_promotion_window=mtd force_lifecycle_bucket_windows=false force_deep_audits=false force_workorder_branch=false runtime_apply_bridge=true scalp_sim_auto_approval_control_tower=true latency_classifier_recommendation=true tuning_performance_control_tower=true swing_lifecycle=true swing_strategy_discovery=true swing_lifecycle_matrix=true swing_lifecycle_bucket_discovery=true swing_ai_review_provider=openai swing_lifecycle_bucket_discovery_ai_provider=openai pattern_lab_ai_review_provider=openai producer_gap_discovery_ai_provider=openai stage_hook_workorder_discovery_ai_provider=openai pattern_labs=true deepseek_swing_lab=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true key_lineage_ledger=true conversion_lane=true next_stage2_checklist=true finished_at=2026-07-22T21:04:46+0900`
- predecessor_status: `pass`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `[]`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker used full/default stage profile`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_no_submit_drought_critical`
  - 근거: `{'status': 'not_applicable', 'handoff_status': 'not_applicable', 'root_cause_closure_status': 'not_applicable', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': False, 'primary': 'LATENCY_DROUGHT', 'matches': ['LATENCY_DROUGHT'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 55, 'submit_drought_refresh_applied_count': 51, 'submit_drought_latency_pass_recovered_count': 15, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 22, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No submit drought critical condition was active in this verification context.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 44, 'affected_rate': 0.1302, 'dimension_counts': {'risk_context_bucket': 41, 'score_bucket': 3, 'price_resolution_bucket': 1}, 'unknown_root_cause_counts': {'risk_context_bucket:source_field_missing': 40, 'score_bucket:source_score_missing': 3, 'risk_context_bucket:post_submit_or_exit_not_required': 1, 'price_resolution_bucket:post_submit_or_exit_not_required': 1}, 'stage_counts': {'scalp_entry_action_decision_snapshot': 228, 'order_bundle_submitted': 22, 'latency_block': 37, 'entry_submit_revalidation_block': 3, 'scalp_sim_pre_submit_liquidity_guard_would_block': 1, 'blocked_ai_score': 5, 'scalp_sim_sell_order_assumed_filled': 1}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 263, 'new_or_unseen_token_vs_prior_adm': 75}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `pass_no_current_handoff_workorder`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'pass', 'ai_review_workorder_count': 0, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 287, 'sim_auto_approved': 2, 'new_bucket_candidate': 12}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 36, 'source_only_observation': 263, 'sim_auto_policy': 2}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 13, 'sim_auto_approved': 43, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 243, 'source_quality_blocker': 358, 'tier2_fail_closed_source_only': 49}, 'source_contract_status': 'warning', 'source_contract_change_count': 12, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 90, 'bridge_blocker_ledger_count': 200, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 708, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 13, 'sim_auto_approved': 43, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 243, 'source_quality_blocker': 358, 'tier2_fail_closed_source_only': 49}, 'positive_edge_source_quality_pass_count': 90, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 223, 'quiet_gap_rollup_count': 223, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 34, 'status': 'pass'}`

## BUY Funnel Submit Drought Handoff
- status: `not_applicable`
- critical: `False`
- missing: `[]`

## Submit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- missing: `[]`

## Holding Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `14` / `14` / `14`
- workorder_count ev/runtime/expected: `5` / `5` / `5`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `27` / `27` / `27`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `494`
- complete_flow_count: `9`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `9`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `485`
- complete_flow_rate: `0.0182`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 111339, 'input_context_chars': 110019, 'input_context_hash': '19c50d18e86239ccd46b04b1abaaf7275b571c9fcbb4c03cd2cb255a0a420b42', 'elapsed_ms': 108612, 'output_chars': 13711, 'input_tokens': 31869, 'output_tokens': 8137, 'total_tokens': 40006, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'entry_split_order_plan', 'holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'scale_in_split_order_plan', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `1`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Scale-In Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`
- policy_contract_status: `pass`
- policy_contract_missing: `[]`
- policy_contract_interpretation: `Scale-in policy contract closed as source-only; runtime remains disabled and reopen trigger is preserved.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['exit:stage_policy:exit_weighted_adm_v1', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'source_contract:source_added:entry:source_key_entry', 'source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `['source_contract:source_added:entry:source_key_entry', 'source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `2` / `2`
- derived input/consumed: `0` / `0`
- derived_contract_drift_recompute_consumed: `False`
- closure_counts: `{'new_parent_candidate_created': 2}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 616, 'recomputable_match_count': 616, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 616}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_1f5bdeeb7e244bcf', 'ldm_refinement_b29819efd76a1b34']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `[]`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `616`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 416), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 200)]`

## Lifecycle Bucket Windows
- status: `warning`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'too_broad', 'parent_bucket_count': 23, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 52, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 44, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `['lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target']`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `['swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_06f90aa5d0', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_15e8086457', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_17be04825a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_191eedf3a5', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_198f2a001c', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1d2a773521', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_3d3815ee75', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_46c89131ff', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_596f246299', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5f1fd88426', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60abfbeb0f', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_65ddf62dd9', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_81439c436f', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8967a32ed7', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_9a16bc8153', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_a56f563c22', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c667aec5d9', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c95c89b312', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d27ece90a1', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dbcdc8c839', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dd9ef30ddd', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e13d2dea57']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `False`
- ai_two_pass_review_status: `parsed`
- warnings: `[]`
- interpretation: `Swing LDM candidates/workorders propagated through EV, runtime summary, workorder, and verifier.`

## Producer Gap Discovery Handoff
- status: `pass`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- expected_workorder_order_ids: `[]`
- missing_workorder_order_ids: `[]`
- missing: `[]`
- interpretation: `producer gap high-priority orders propagated to code improvement workorder with parsed AI review`

## Stage Hook Workorder Handoff
- status: `pass`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- expected_workorder_order_ids: `['order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard', 'order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe']`
- missing_workorder_order_ids: `[]`
- unconsumed_hook_candidate_ids: `[]`
- missing: `[]`
- interpretation: `stage hook implementation-ready orders propagated to code improvement workorder`

## Bottom Rebound Sim Handoff
- status: `pass`
- included: `True`
- source_rows: `40`
- selected_candidate_count: `33`
- arm_count: `99`
- persisted_candidate_count: `33`
- persisted_arm_count: `99`
- missing: `[]`
- interpretation: `bottom_rebound source candidates were selected, armed, and persisted for label/EV handoff`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-07-22-c07187106752`
- source_hash: `c07187106752208c0f4dd60b3f0470970bb52c41c0c1fc211f3bd3c0474b9da3`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-07-22-a6b22cd0fbb6`
- previous_source_hash: `a6b22cd0fbb6618cb7ffd5655e3bbe213c12cf104cfc4dffb854b88b87c91478`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
