# Threshold Cycle Postclose Verification - 2026-06-09

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-06-09 max_iterations=80 started_at=2026-06-09T15:45:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-06-09 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false finished_at=2026-06-09T16:57:17+0900`
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

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 619, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'code_patch_required': 3, 'runtime_blocked_contract_gap': 30, 'sim_auto_approved': 39, 'source_only_keep_collecting': 45, 'source_quality_blocker': 501, 'tier2_fail_closed_source_only': 1}, 'positive_edge_source_quality_pass_count': 11, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 281, 'quiet_gap_rollup_count': 281, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 56, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `35` / `35` / `35`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `62` / `62` / `62`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `18944`
- complete_flow_count: `137`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `137`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `18807`
- complete_flow_rate: `0.0072`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_submit`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 88091, 'input_context_chars': 86771, 'input_context_hash': 'c618a385e810ca5416420190f036c3e08f37b3badc20e5e80d9600fc45681d4b', 'elapsed_ms': 118373, 'output_chars': 10412, 'input_tokens': 25189, 'output_tokens': 6418, 'total_tokens': 31607, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'holding_flow_ofi_smoothing', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `16`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `['entry_bucket_10', 'entry_bucket_11', 'entry_bucket_2', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_8', 'entry_bucket_9']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM entry bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Scale-In Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `['scale_in_bucket_1', 'scale_in_bucket_10', 'scale_in_bucket_2', 'scale_in_bucket_3', 'scale_in_bucket_4', 'scale_in_bucket_5', 'scale_in_bucket_6', 'scale_in_bucket_7', 'scale_in_bucket_8', 'scale_in_bucket_9']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `['overnight_bucket_10', 'overnight_bucket_11', 'overnight_bucket_2', 'overnight_bucket_4', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_9']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:chosen_action:wait_requote', 'entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov', 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_watch_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_stale_block_liquidity_l', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_stale_watch_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_stale_watch_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_stale_block_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_stale_watch_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_bottoming_entry_allowed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_block_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'scale_in:ai_score_band:score_60_62', 'scale_in:ai_score_band:score_lt60', 'scale_in:ai_score_source:score_field_backfilled', 'scale_in:arm:avg_down', 'scale_in:arm:pyramid', 'scale_in:blocker_namespace:avg_down', 'scale_in:blocker_namespace:avg_down_only', 'scale_in:blocker_namespace:pyramid', 'scale_in:blocker_reason:low_broken', 'scale_in:blocker_reason:ok', 'scale_in:blocker_reason:pnl_out_of_range_0_71', 'scale_in:blocker_reason:pnl_out_of_range_0_72', 'scale_in:blocker_reason:pnl_out_of_range_0_75', 'scale_in:blocker_reason:pnl_out_of_range_0_77', 'scale_in:blocker_reason:pnl_out_of_range_0_81', 'scale_in:blocker_reason:pnl_out_of_range_0_85', 'scale_in:blocker_reason:pnl_out_of_range_0_86', 'scale_in:blocker_reason:pnl_out_of_range_0_88', 'scale_in:blocker_reason:pnl_out_of_range_0_89', 'scale_in:blocker_reason:pnl_out_of_range_0_92', 'scale_in:blocker_reason:pnl_out_of_range_0_93', 'scale_in:blocker_reason:pnl_out_of_range_0_94', 'scale_in:blocker_reason:pnl_out_of_range_0_95', 'scale_in:blocker_reason:pnl_out_of_range_0_99', 'scale_in:blocker_reason:pnl_out_of_range_1_00', 'scale_in:blocker_reason:pnl_out_of_range_1_01', 'scale_in:blocker_reason:pnl_out_of_range_1_04', 'scale_in:blocker_reason:pnl_out_of_range_1_13', 'scale_in:blocker_reason:pnl_out_of_range_1_15', 'scale_in:blocker_reason:pnl_out_of_range_1_16', 'scale_in:blocker_reason:pnl_out_of_range_1_18', 'scale_in:blocker_reason:pnl_out_of_range_1_30', 'scale_in:blocker_reason:pnl_out_of_range_1_42', 'scale_in:blocker_reason:profit_not_enough', 'scale_in:blocker_reason:scalp_sim_panic_scale_in_blocked', 'scale_in:blocker_reason:trend_not_strong']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `4` / `4`
- closure_counts: `{'absorbed_into_existing_parent': 2, 'new_parent_candidate_created': 1, 'parent_refinement_candidate_created': 1}`
- missing: `[]`
- warnings: `[]`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_7f6d6ffe442e2c99', 'ldm_refinement_c31f72d5895b9bf9']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `warning`
- active_seed_ids: `['active_seed_03c539e6527cdda2', 'active_seed_136f942c5ddd1131', 'active_seed_44e1edd653df5f36', 'active_seed_5de7caf844ddc438', 'active_seed_5fbf3e3baf24631e', 'active_seed_7cf1c198fc1e5246', 'active_seed_a0e7fe5858bd147e', 'active_seed_b99a2dea7aac2a83']`
- observed_seed_ids: `['active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83']`
- missing: `[]`
- warnings: `['active_sim_priority_preopen_handoff_pending']`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `8315`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 6077), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 1515), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 470), ('{"entry_score_parent": "score_high_confirmation", "entry_source_parent": "entry_source_wait6579"}', 131), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 122)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 30}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 38}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 38}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `[]`
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
- status: `not_applicable`
- included: `False`
- source_rows: `0`
- selected_candidate_count: `0`
- arm_count: `0`
- persisted_candidate_count: `0`
- persisted_arm_count: `0`
- missing: `[]`
- interpretation: `bottom_rebound source was absent or blocked; safe-pool-only swing sim path applies`

## Workorder Snapshot
- generation_id: `2026-06-09-89c1ff3a4e65`
- source_hash: `89c1ff3a4e65978d3b4a4737c953070dd70d5e73bcff90c7ebeadada5408b000`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-06-09-f5f75a582319`
- previous_source_hash: `f5f75a58231964d0f88be1870bf56c7d3a0221fadf905175ecc648c483cbe6de`
- new_order_ids: `[]`
- removed_order_ids: `['order_pattern_lab_ai_review_ai_review_gap']`
- decision_changed_order_ids: `[]`
