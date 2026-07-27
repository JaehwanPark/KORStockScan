# Threshold Cycle Postclose Verification - 2026-07-27

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-07-27 max_iterations=80 started_at=2026-07-27T21:43:48+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-07-27 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false finished_at=2026-07-28T01:09:24+0900`
- predecessor_status: `pass`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `[]`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker was produced by controller recovery action `tail_repair_done_reconciliation`; execution flags are not asserted by this marker`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_handoff_closed`
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 27, 'submit_drought_refresh_applied_count': 19, 'submit_drought_latency_pass_recovered_count': 3, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 2, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 21, 'affected_rate': 0.1273, 'dimension_counts': {'risk_context_bucket': 21, 'price_resolution_bucket': 1}, 'unknown_root_cause_counts': {'risk_context_bucket:source_field_missing': 19, 'risk_context_bucket:post_submit_or_exit_not_required': 2, 'price_resolution_bucket:post_submit_or_exit_not_required': 1}, 'stage_counts': {'scalp_entry_action_decision_snapshot': 71, 'latency_block': 15, 'blocked_ai_score': 3, 'order_bundle_submitted': 2, 'scalp_sim_sell_order_assumed_filled': 1}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'-': 89, 'advisory_only_stage_without_prior_lookup': 32, 'new_or_unseen_token_vs_prior_adm': 38, 'matched_prior_bucket': 6}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `pass_no_current_handoff_workorder`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'pass', 'ai_review_workorder_count': 0, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 151, 'runtime_blocked_contract_gap': 2, 'new_bucket_candidate': 10}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 25, 'source_only_observation': 136, 'source_quality_gap': 2}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 8, 'sim_auto_approved': 38, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 220, 'source_quality_blocker': 347, 'tier2_fail_closed_source_only': 80}, 'source_contract_status': 'warning', 'source_contract_change_count': 12, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 118, 'bridge_blocker_ledger_count': 200, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 695, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 8, 'sim_auto_approved': 38, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 220, 'source_quality_blocker': 347, 'tier2_fail_closed_source_only': 80}, 'positive_edge_source_quality_pass_count': 118, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 111, 'quiet_gap_rollup_count': 111, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 23, 'status': 'pass'}`

## BUY Funnel Submit Drought Handoff
- status: `pass`
- critical: `True`
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
- bucket_count ev/runtime/expected: `5` / `5` / `5`
- workorder_count ev/runtime/expected: `0` / `0` / `0`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `5` / `5` / `5`
- workorder_count ev/runtime/expected: `0` / `0` / `0`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `warning`
- attribution_present: `True`
- flow_count: `64`
- complete_flow_count: `0`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `0`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `64`
- complete_flow_rate: `0.0`
- join_contract_blocked: `True`
- bundle_ev_tuning_state: `blocked_join_gap`
- top_incomplete_reason: `missing_holding`
- missing: `['lifecycle_complete_flow_absent', 'lifecycle_join_contract_blocked']`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 109174, 'input_context_chars': 107854, 'input_context_hash': '30241dba5cb72b5971d006f351cf3c47389e172cf7ad297cce245fbd2e7f651f', 'elapsed_ms': 96086, 'output_chars': 12630, 'input_tokens': 31311, 'output_tokens': 7493, 'total_tokens': 38804, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'entry_split_order_plan', 'holding_exit_decision_matrix_advisory', 'protect_trailing_smoothing', 'scale_in_split_order_plan', 'soft_stop_whipsaw_confirmation']`
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
- expected_candidate_ids: `['lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'source_contract:source_added:entry:source_key_entry', 'source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `['source_contract:source_added:entry:source_key_entry', 'source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `0` / `0`
- derived input/consumed: `0` / `0`
- derived_contract_drift_recompute_consumed: `False`
- closure_counts: `{}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 0, 'recomputable_match_count': 0, 'recomputable_hypothesis_ids': [], 'runtime_matched_event_count': 0}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `[]`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `[]`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `0`
- top_candidate_prefixes: `[]`

## Lifecycle Bucket Windows
- status: `warning`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'too_broad', 'parent_bucket_count': 18, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'too_broad', 'parent_bucket_count': 27, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 44, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `['lifecycle_bucket_confirmation_windows_not_target', 'lifecycle_bucket_discovery_rolling10d_parent_granularity_not_target', 'lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target']`

## Swing Lifecycle Handoff
- status: `warning`
- expected_candidate_ids: `['swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_06f90aa5d0', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_15e8086457', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_17be04825a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1d2a773521', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_46c89131ff', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_596f246299', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5f1fd88426', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60abfbeb0f', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_65ddf62dd9', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7480cc41ef', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_77884348b4', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8070f782ab', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_81439c436f', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8967a32ed7', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_a56f563c22', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b74bbc500a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c95c89b312', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ccc3dfa9db', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d105b725f2', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d27ece90a1', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dbcdc8c839', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e13d2dea57']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `False`
- ai_two_pass_review_status: `partial`
- warnings: `['swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_source_only', 'swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_required_source_only', 'swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_sim_auto_blocked', 'swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_fail_closed']`
- interpretation: `Swing LDM AI two-pass review is fail-closed; sim-auto promotion is blocked and must be surfaced.`

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
- status: `not_applicable`
- included: `False`
- source_rows: `0`
- selected_candidate_count: `0`
- arm_count: `0`
- persisted_candidate_count: `0`
- persisted_arm_count: `0`
- missing: `[]`
- interpretation: `bottom_rebound source was absent or blocked; safe-pool-only swing sim path applies`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-07-27-908dfabd25f0`
- source_hash: `908dfabd25f09ed390dcc3be09181a194ab12899d7f2a53b29f03099b686e3bb`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-07-27-84b3f34b5b6f`
- previous_source_hash: `84b3f34b5b6f744a5cffa26b33bc6d5f5c95b97adebe82df6466d43cec38ba59`
- new_order_ids: `[]`
- removed_order_ids: `['order_observation_source_quality_unknown_token_provenance_gap', 'order_pattern_lab_ai_review_lifecycle_decision_matrix_all_stage_below_sample_floor', 'order_pattern_lab_ai_review_pattern_lab_propagation_audit_missing', 'order_pattern_lab_ai_review_scalp_entry_adm_sample_floor_gap', 'order_pattern_lab_ai_review_swing_clean_tuning_baseline_lookback_filtered', 'order_pattern_lab_ai_review_swing_intraday_live_equiv_probe_missing', 'order_pattern_lab_ai_review_swing_strategy_discovery_pending_quotes']`
- decision_changed_order_ids: `[]`
