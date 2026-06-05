# Threshold Cycle Postclose Verification - 2026-06-05

- status: `pass`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-06-05 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false started_at=2026-06-05T18:56:32+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-06-05 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false finished_at=2026-06-05T18:56:32+0900`
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
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 520, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'code_patch_required': 5, 'runtime_blocked_contract_gap': 26, 'sim_auto_approved': 110, 'source_only_keep_collecting': 4, 'source_quality_blocker': 375}, 'positive_edge_source_quality_pass_count': 10, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 199, 'quiet_gap_rollup_count': 199, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 46, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `32` / `32` / `32`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `48` / `48` / `48`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `12294`
- complete_flow_count: `56`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `56`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `12238`
- complete_flow_rate: `0.0046`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_submit`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'reused_valid_artifact', 'new_provider_call': False, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 113246, 'input_context_chars': 111926, 'input_context_hash': 'b5b5e4831927809071bda260620aea7ad3f98ddf92563374c1466f52fbeb183d', 'elapsed_ms': 120405, 'output_chars': 13217, 'input_tokens': 31752, 'output_tokens': 7140, 'total_tokens': 38892, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract', 'reuse_source_path': '/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-06-05_postclose.json', 'reused_at': '2026-06-05 17:57:20', 'estimated_incremental_cost': 0.0, 'estimated_incremental_cost_usd': 0.0, 'incremental_cost_status': 'reused_no_new_provider_call'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'holding_flow_ofi_smoothing', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `14`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `['entry_bucket_2', 'entry_bucket_3', 'entry_bucket_4', 'entry_bucket_5', 'entry_bucket_6']`
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
- expected_candidate_ids: `['overnight_bucket_11', 'overnight_bucket_12', 'overnight_bucket_13', 'overnight_bucket_3', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_8']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `pass`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:chosen_action:wait_requote', 'entry:liquidity_bucket:liquidity_high', 'entry:overbought_bucket:overbought_normal', 'entry:source_stage:wait6579_ev_cohort', 'entry:stale_bucket:fresh_or_unflagged', 'entry:strength_bucket:strong_strength_momentum', 'entry:strength_bucket:weak_strength_momentum', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_bottoming_entry_allowed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_pass_revalidation_block_fa', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'scale_in:ai_score_band:score_60_62', 'scale_in:ai_score_band:score_63_65', 'scale_in:ai_score_band:score_66_69', 'scale_in:ai_score_band:score_70p', 'scale_in:ai_score_band:score_lt60', 'scale_in:ai_score_source:score_field_backfilled', 'scale_in:arm:avg_down', 'scale_in:arm:pyramid', 'scale_in:blocker_namespace:avg_down', 'scale_in:blocker_namespace:avg_down_only', 'scale_in:blocker_namespace:pyramid', 'scale_in:blocker_reason:add_judgment_locked', 'scale_in:blocker_reason:ai_not_recovering', 'scale_in:blocker_reason:hold_sec_out_of_range_227s', 'scale_in:blocker_reason:low_broken', 'scale_in:blocker_reason:ok', 'scale_in:blocker_reason:pnl_out_of_range_0_71', 'scale_in:blocker_reason:pnl_out_of_range_0_72', 'scale_in:blocker_reason:pnl_out_of_range_0_73', 'scale_in:blocker_reason:pnl_out_of_range_0_74', 'scale_in:blocker_reason:pnl_out_of_range_0_75', 'scale_in:blocker_reason:pnl_out_of_range_0_76', 'scale_in:blocker_reason:pnl_out_of_range_0_77', 'scale_in:blocker_reason:pnl_out_of_range_0_78', 'scale_in:blocker_reason:pnl_out_of_range_0_79', 'scale_in:blocker_reason:pnl_out_of_range_0_80', 'scale_in:blocker_reason:pnl_out_of_range_0_81', 'scale_in:blocker_reason:pnl_out_of_range_0_82', 'scale_in:blocker_reason:pnl_out_of_range_0_83', 'scale_in:blocker_reason:pnl_out_of_range_0_84', 'scale_in:blocker_reason:pnl_out_of_range_0_85', 'scale_in:blocker_reason:pnl_out_of_range_0_86', 'scale_in:blocker_reason:pnl_out_of_range_0_87', 'scale_in:blocker_reason:pnl_out_of_range_0_88', 'scale_in:blocker_reason:pnl_out_of_range_0_89', 'scale_in:blocker_reason:pnl_out_of_range_0_90', 'scale_in:blocker_reason:pnl_out_of_range_0_91', 'scale_in:blocker_reason:pnl_out_of_range_0_92', 'scale_in:blocker_reason:pnl_out_of_range_0_93', 'scale_in:blocker_reason:pnl_out_of_range_0_94', 'scale_in:blocker_reason:pnl_out_of_range_0_95', 'scale_in:blocker_reason:pnl_out_of_range_0_96', 'scale_in:blocker_reason:pnl_out_of_range_0_97', 'scale_in:blocker_reason:pnl_out_of_range_0_98', 'scale_in:blocker_reason:pnl_out_of_range_0_99', 'scale_in:blocker_reason:pnl_out_of_range_1_00', 'scale_in:blocker_reason:pnl_out_of_range_1_01', 'scale_in:blocker_reason:pnl_out_of_range_1_02', 'scale_in:blocker_reason:pnl_out_of_range_1_03', 'scale_in:blocker_reason:pnl_out_of_range_1_04', 'scale_in:blocker_reason:pnl_out_of_range_1_05', 'scale_in:blocker_reason:pnl_out_of_range_1_06', 'scale_in:blocker_reason:pnl_out_of_range_1_07', 'scale_in:blocker_reason:pnl_out_of_range_1_08', 'scale_in:blocker_reason:pnl_out_of_range_1_09', 'scale_in:blocker_reason:pnl_out_of_range_1_11', 'scale_in:blocker_reason:pnl_out_of_range_1_12', 'scale_in:blocker_reason:pnl_out_of_range_1_13', 'scale_in:blocker_reason:pnl_out_of_range_1_14', 'scale_in:blocker_reason:pnl_out_of_range_1_15', 'scale_in:blocker_reason:pnl_out_of_range_1_16', 'scale_in:blocker_reason:pnl_out_of_range_1_17', 'scale_in:blocker_reason:pnl_out_of_range_1_18', 'scale_in:blocker_reason:pnl_out_of_range_1_19', 'scale_in:blocker_reason:pnl_out_of_range_1_20', 'scale_in:blocker_reason:pnl_out_of_range_1_21', 'scale_in:blocker_reason:pnl_out_of_range_1_22', 'scale_in:blocker_reason:pnl_out_of_range_1_23', 'scale_in:blocker_reason:pnl_out_of_range_1_24', 'scale_in:blocker_reason:pnl_out_of_range_1_25', 'scale_in:blocker_reason:pnl_out_of_range_1_26', 'scale_in:blocker_reason:pnl_out_of_range_1_27', 'scale_in:blocker_reason:pnl_out_of_range_1_28', 'scale_in:blocker_reason:pnl_out_of_range_1_29', 'scale_in:blocker_reason:pnl_out_of_range_1_30', 'scale_in:blocker_reason:pnl_out_of_range_1_31', 'scale_in:blocker_reason:pnl_out_of_range_1_32', 'scale_in:blocker_reason:pnl_out_of_range_1_33', 'scale_in:blocker_reason:pnl_out_of_range_1_34', 'scale_in:blocker_reason:pnl_out_of_range_1_35', 'scale_in:blocker_reason:pnl_out_of_range_1_36', 'scale_in:blocker_reason:pnl_out_of_range_1_37', 'scale_in:blocker_reason:pnl_out_of_range_1_38', 'scale_in:blocker_reason:pnl_out_of_range_1_39', 'scale_in:blocker_reason:pnl_out_of_range_1_40', 'scale_in:blocker_reason:pnl_out_of_range_1_41', 'scale_in:blocker_reason:pnl_out_of_range_1_42', 'scale_in:blocker_reason:pnl_out_of_range_1_43', 'scale_in:blocker_reason:pnl_out_of_range_1_44', 'scale_in:blocker_reason:pnl_out_of_range_1_45', 'scale_in:blocker_reason:pnl_out_of_range_1_46', 'scale_in:blocker_reason:pnl_out_of_range_1_47', 'scale_in:blocker_reason:pnl_out_of_range_1_48', 'scale_in:blocker_reason:pnl_out_of_range_1_49', 'scale_in:blocker_reason:pnl_out_of_range_1_51', 'scale_in:blocker_reason:pnl_out_of_range_1_52', 'scale_in:blocker_reason:pnl_out_of_range_1_53', 'scale_in:blocker_reason:pnl_out_of_range_1_54', 'scale_in:blocker_reason:pnl_out_of_range_1_55', 'scale_in:blocker_reason:pnl_out_of_range_1_56', 'scale_in:blocker_reason:pnl_out_of_range_1_57', 'scale_in:blocker_reason:pnl_out_of_range_1_58', 'scale_in:blocker_reason:pnl_out_of_range_1_61', 'scale_in:blocker_reason:pnl_out_of_range_1_64', 'scale_in:blocker_reason:pnl_out_of_range_1_68', 'scale_in:blocker_reason:profit_not_enough', 'scale_in:blocker_reason:scalp_sim_panic_scale_in_blocked', 'scale_in:blocker_reason:scalping_cutoff']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `[]`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `3` / `3`
- closure_counts: `{'new_parent_candidate_created': 3}`
- missing: `[]`
- warnings: `[]`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `[]`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `not_applicable`
- active_seed_ids: `[]`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `10116`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 7261), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_observed_other"}', 2350), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 505)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 48}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 48}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 48}}`
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
- expected_workorder_order_ids: `[]`
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
- generation_id: `2026-06-05-b446a9bab953`
- source_hash: `b446a9bab953353079ef48cb55fb1de3ab05b00c94d1e1a0e316dc95207f861f`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-06-05-885e5d311ed8`
- previous_source_hash: `885e5d311ed8e8744b3c8de69d0fcbba9238491bbc67165df2d366ab034d8fda`
- new_order_ids: `['order_pattern_lab_ai_review_code_improvement_workorder']`
- removed_order_ids: `['order_holding_exit_decision_matrix_edge_counterfactual', 'order_pattern_lab_ai_review_code_improvement_workorder_unimplemented', 'order_pattern_lab_ai_review_scalping_reentry_missing', 'order_pattern_lab_ai_review_swing_reentry_missing', 'order_pattern_lab_ai_review_threshold_cycle_ev_missing', 'order_pattern_lab_currentness_audit_scalping_ldm_threshold_reentry_sources', 'order_pattern_lab_currentness_audit_swing_ldm_threshold_reentry_sources', 'order_stage_hook_workorder_discovery_stage_hook_holding_flow_runner_debounce_guard', 'order_stage_hook_workorder_discovery_stage_hook_plateau_breakdown_exit_arbitration_probe']`
- decision_changed_order_ids: `[]`
