# Threshold Cycle Postclose Verification - 2026-05-19

- status: `fail`
- latest_start_marker: `-`
- latest_done_marker: `-`
- predecessor_status: `fail`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['ldm_lifecycle_flow_bucket_handoff_missing', 'lifecycle_bucket_windows_fail', 'lifecycle_complete_flow_absent', 'postclose_start_marker_missing']`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest START marker has no matching DONE marker`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `['runtime_apply_gap_audit_failed']`

## Runtime Apply Gap Audit
- status: `fail`
- retry_queue_count: `2`
- codex_directive_count: `2`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'candidate_count': 1, 'codex_directive_count': 2, 'critical_failure_count': 2, 'derived_review_category_counts': {'source_quality_blocker': 1}, 'positive_edge_source_quality_pass_count': 0, 'quiet_gap_codex_directive_count': 1, 'quiet_gap_count': 2, 'quiet_gap_rollup_count': 2, 'retry_queue_count': 2, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 0, 'status': 'fail'}`

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
- bucket_count ev/runtime/expected: `28` / `28` / `28`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `41` / `41` / `41`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `fail`
- attribution_present: `True`
- flow_count: `13652`
- complete_flow_count: `0`
- incomplete_flow_count: `0`
- complete_flow_rate: `0.0`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `None`
- top_incomplete_reason: `None`
- missing: `['lifecycle_complete_flow_absent']`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'attempted_keys': 2, 'attempted_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'holding_flow_ofi_smoothing', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `13`
- active_undecided_count: `0`
- decision_coverage_rate: `None`
- source_quality_status: `missing`
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
- expected_candidate_ids: `['scale_in_bucket_10', 'scale_in_bucket_11', 'scale_in_bucket_12', 'scale_in_bucket_2', 'scale_in_bucket_3', 'scale_in_bucket_4', 'scale_in_bucket_6', 'scale_in_bucket_7', 'scale_in_bucket_8', 'scale_in_bucket_9']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

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
- status: `missing`
- source_contract_status: `-`
- ai_two_pass_review_status: `-`
- expected_candidate_ids: `[]`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `[]`
- interpretation: `lifecycle bucket discovery report missing`

## Lifecycle Bucket Windows
- status: `fail`
- checked: `True`
- windows: `{'rolling5d': {'available': False}, 'rolling10d': {'available': False}, 'mtd': {'available': False}}`
- missing: `['lifecycle_bucket_discovery_mtd_missing', 'lifecycle_bucket_discovery_rolling10d_missing', 'lifecycle_bucket_discovery_rolling5d_missing', 'lifecycle_decision_matrix_mtd_missing', 'lifecycle_decision_matrix_rolling10d_missing', 'lifecycle_decision_matrix_rolling5d_missing']`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `['swing_bucket_entry_entry_bucket_attribution_blocked_gatekeeper_reject_breakout_flat_up_75_84_vpw_extreme_kospi_4007652a0d7c', 'swing_bucket_entry_entry_bucket_attribution_blocked_gatekeeper_reject_kospi_base_flat_up_75_84_vpw_extreme_kosp_ed91b207174e', 'swing_bucket_entry_entry_bucket_attribution_blocked_gatekeeper_reject_kospi_base_flat_up_lt55_vpw_extreme_kospi_f0dd798d0126', 'swing_bucket_entry_entry_bucket_attribution_blocked_gatekeeper_reject_kospi_base_gap_down_lt55_vpw_extreme_kosp_7d5d02359973', 'swing_bucket_entry_entry_bucket_attribution_blocked_swing_gap_breakout_gap_up_missing_vpw_extreme_kospi_ml_sim_b5bddbabc7c8', 'swing_bucket_entry_entry_bucket_attribution_blocked_swing_gap_meta_v2_gap_up_missing_vpw_extreme_kospi_ml_sim_v_9e69f7359208', 'swing_bucket_entry_entry_bucket_attribution_blocked_swing_score_vpw_breakout_gap_down_large_lt55_vpw_extreme_ko_7b14638b2b46', 'swing_bucket_entry_entry_bucket_attribution_blocked_swing_score_vpw_kospi_base_flat_up_lt55_vpw_extreme_kospi_m_0e2fe0c1982f', 'swing_bucket_entry_entry_bucket_attribution_blocked_swing_score_vpw_kospi_base_gap_down_large_lt55_vpw_extreme_ae569b16b6dd', 'swing_bucket_entry_entry_bucket_attribution_missing_55_64_missing_kospi_ml', 'swing_bucket_entry_entry_bucket_attribution_missing_65_74_missing_kospi_ml', 'swing_bucket_entry_entry_bucket_attribution_missing_lt55_missing_kospi_ml', 'swing_bucket_entry_entry_bucket_attribution_missing_missing_missing_kospi_ml', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_deep_neg_missing_2h_1d_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_deep_neg_missing_ge_1d_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_deep_neg_missing_held_missing_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_missing_2h_1d_kospi_trailing_start_take_profit', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_high_missing_held_missing_kospi_trailing_start_take_profit', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_2h_1d_kospi_trailing_start_take_profit', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_30m_2h_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_trailing_start_take_profit', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_2h_1d_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_30m_2h_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss', 'swing_bucket_holding_exit_holding_exit_bucket_attribution_missing_missing_held_missing', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_scale_in_none_0d1fb5babf85', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_scale_in_none_1b1c218431ac', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_scale_in_none_9569ff80981e', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_scale_in_none_ed12bcbf8c3a', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_entry_missing_holding_holding_missing_scale_in_swing_scale_in_0826ffce2d74', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_gatekeeper_rejec_24a673483881', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_gatekeeper_rejec_26e3f919d949', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_gatekeeper_rejec_2a3c6dcc9740', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_gatekeeper_rejec_34d005fea636', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_gap_breako_b0a324fdaa50', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_gap_meta_v_8627fb64111b', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_48621dcefea7', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_6f229637116f', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_7a617f53f6eb', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_9e727379dbb5', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_d9f8c415be7a', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_blocked_swing_score_vpw_f64f91f8d683', 'swing_bucket_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_missing_lt55_missing_kos_83089d4872d5', 'swing_bucket_scale_in_scale_in_bucket_attribution_avg_down_instrumentation_gap_swing_dynamic_allowed_market']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `False`
- ai_two_pass_review_status: `parsed`
- warnings: `[]`
- interpretation: `Swing LDM candidates/workorders propagated through EV, runtime summary, workorder, and verifier.`

## Producer Gap Discovery Handoff
- status: `missing`
- ai_two_pass_review_status: `missing`
- audit_status: `-`
- expected_workorder_order_ids: `[]`
- missing_workorder_order_ids: `[]`
- missing: `[]`
- interpretation: `producer_gap_discovery artifact missing`

## Stage Hook Workorder Handoff
- status: `missing`
- ai_two_pass_review_status: `missing`
- audit_status: `-`
- expected_workorder_order_ids: `[]`
- missing_workorder_order_ids: `[]`
- unconsumed_hook_candidate_ids: `[]`
- missing: `[]`
- interpretation: `stage_hook_workorder_discovery artifact missing`

## Bottom Rebound Sim Handoff
- status: `missing`
- included: `False`
- source_rows: `0`
- selected_candidate_count: `0`
- arm_count: `0`
- persisted_candidate_count: `0`
- persisted_arm_count: `0`
- missing: `['swing_strategy_discovery_sim_missing']`
- interpretation: `swing_strategy_discovery_sim artifact missing`

## Workorder Snapshot
- generation_id: `2026-05-19-2eb72a1123d0`
- source_hash: `2eb72a1123d056c6ac71c4782b8293a727bb9b3eec2365acd1d43be2bb52ea7b`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-05-19-0f9672e3e90c`
- previous_source_hash: `0f9672e3e90c91ea57e6691823231067a70f64e5f7ed8e34c4a77df5363764c4`
- new_order_ids: `['order_entry_sim_submit_path_bucket_instrumentation', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_7b698c08', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_sell_order_assumed_filled_rule_scalp_sim_overnight_sel_7a368c73', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_sell_order_assumed_filled_rule_scalp_sim_overnight_sel_cf4ef5d4', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_02d0d660', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_0b5e3447', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_trailing_take_profit_outcome_eb03513e', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b97f847f', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_70c74920', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6af12dd1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_85a4bb2f', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_6af12dd1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_ffbb2a48', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_32463a04', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_85a4bb2f', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b97f847f', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_buy_profit_profit_pos150_pos300_92355b6c', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_9c31b140', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c6db79d9', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_unknown_profit_p_c9a72bc6', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_cfc98129', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg010_pos08_9ba67c14', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_173986ed', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_98664069', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_8a305aa1', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_f6d831c4', 'order_lifecycle_overnight_bucket_peak_profit_band_peak_lt_zero', 'order_lifecycle_overnight_bucket_profit_band_profit_lt_neg070', 'order_lifecycle_overnight_bucket_profit_band_profit_neg070_neg010', 'order_lifecycle_scale_in_bucket_ai_score_band_score_unknown', 'order_lifecycle_scale_in_bucket_arm_pyramid', 'order_lifecycle_scale_in_bucket_blocker_namespace_avg_down_only', 'order_lifecycle_scale_in_bucket_blocker_namespace_blocker_namespace_unknown', 'order_lifecycle_scale_in_bucket_blocker_namespace_pyramid', 'order_lifecycle_scale_in_bucket_blocker_reason_add_judgment_locked', 'order_lifecycle_scale_in_bucket_blocker_reason_holding_exit_matrix_avg_down_bias', 'order_lifecycle_scale_in_bucket_blocker_reason_low_broken', 'order_lifecycle_scale_in_bucket_blocker_reason_scalping_cutoff', 'order_lifecycle_scale_in_bucket_blocker_reason_scalping_pyramid_ok', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_2h_1d_kospi_trailing_start_take_profit', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_low_missing_held_missing_kospi_trailing_start_take_profit', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_2h_1d_kospi_regime_stop_loss', 'order_swing_ldm_holding_exit_holding_exit_bucket_attribution_mfe_neg_missing_held_missing_kospi_regime_stop_loss']`
- removed_order_ids: `['order_ai_threshold_dominance', 'order_ai_threshold_miss_ev_recovery', 'order_latency_guard_miss_ev_recovery', 'order_perf_buy_funnel_json_scan', 'order_perf_daily_report_bulk_history', 'order_perf_daily_report_engine_singleton', 'order_perf_recommend_update_vectorization', 'order_perf_swing_simulation_iteration', 'order_swing_gatekeeper_reject_threshold_review', 'order_swing_ofi_qi_stale_or_missing_context', 'order_swing_pattern_lab_deepseek_ofi_qi_stale_missing', 'order_swing_pattern_lab_deepseek_scale_in_events_observed']`
- decision_changed_order_ids: `[]`
