# Threshold Cycle Postclose Verification - 2026-07-14

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-07-14 max_iterations=80 started_at=2026-07-14T20:10:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-07-14 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false finished_at=2026-07-14T21:33:42+0900`
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
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 28, 'submit_drought_refresh_applied_count': 23, 'submit_drought_latency_pass_recovered_count': 5, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 5, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 10, 'affected_rate': 0.082, 'dimension_counts': {'score_bucket': 1, 'risk_context_bucket': 9, 'price_resolution_bucket': 1}, 'unknown_root_cause_counts': {'score_bucket:source_score_missing': 1, 'risk_context_bucket:post_submit_or_exit_not_required': 1, 'price_resolution_bucket:post_submit_or_exit_not_required': 1, 'risk_context_bucket:source_field_missing': 8}, 'stage_counts': {'scalp_entry_action_decision_snapshot': 51, 'blocked_ai_score': 15, 'scalp_sim_pre_submit_liquidity_guard_would_block': 8, 'order_bundle_submitted': 5, 'entry_submit_revalidation_block': 1, 'scalp_sim_sell_order_assumed_filled': 1, 'latency_block': 13}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 89, 'new_or_unseen_token_vs_prior_adm': 33}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `pass_no_current_handoff_workorder`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'pass', 'ai_review_workorder_count': 0, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 294, 'sim_auto_approved': 2, 'runtime_blocked_contract_gap': 1, 'new_bucket_candidate': 10}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 40, 'source_only_observation': 264, 'sim_auto_policy': 2, 'source_quality_gap': 1}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 16, 'sim_auto_approved': 45, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 185, 'source_quality_blocker': 413, 'tier2_fail_closed_source_only': 41}, 'source_contract_status': 'warning', 'source_contract_change_count': 12, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 85, 'bridge_blocker_ledger_count': 200, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 702, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 16, 'sim_auto_approved': 45, 'source_only_explicit_exclusion': 2, 'source_only_keep_collecting': 185, 'source_quality_blocker': 413, 'tier2_fail_closed_source_only': 41}, 'positive_edge_source_quality_pass_count': 85, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 237, 'quiet_gap_rollup_count': 237, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 37, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `11` / `11` / `11`
- workorder_count ev/runtime/expected: `0` / `0` / `0`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `19` / `19` / `19`
- workorder_count ev/runtime/expected: `9` / `9` / `9`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `421`
- complete_flow_count: `16`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `16`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `405`
- complete_flow_rate: `0.038`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 110746, 'input_context_chars': 109426, 'input_context_hash': '9559218ab928b0e6dd1426ad1611c1e323576b47fabb01fb24f686a8f2559928', 'elapsed_ms': 65962, 'output_chars': 9889, 'input_tokens': 31641, 'output_tokens': 5314, 'total_tokens': 36955, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'scale_in_split_order_plan', 'soft_stop_whipsaw_confirmation']`
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
- expected_candidate_ids: `['exit:stage_policy:exit_weighted_adm_v1', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'scale_in:stage_policy:scale_in_weighted_adm_v1', 'source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `['source_contract:source_added:institutional_flow_context:source_key_institutional_flow_context', 'source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution', 'source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution', 'source_contract:source_added:scale_in_counterfactual_enrichment:source_key_scale_in_counterfactual_enrichment', 'source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding', 'source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight', 'source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic', 'source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in', 'source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit', 'source_contract:source_added:sim_post_sell:source_key_sim_post_sell', 'source_contract:source_added:wait6579:source_key_wait6579']`
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
- contract_drift: `{'candidate_feature_event_count': 632, 'recomputable_match_count': 632, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 632}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_e54f262dec6c6427', 'ldm_refinement_f7f055037f746a51']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `['active_seed_7cf1c198fc1e5246', 'active_seed_dcd8fdaa26695704']`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `632`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 406), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 226)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 47, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 31, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 36, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `['swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_17be04825a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1b4afcfd76', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_1d2a773521', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_233b41eefb', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_2be2511dbe', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4171503214', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_46c89131ff', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_53dd26ec9c', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_596f246299', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5ea568a2cc', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_5f1fd88426', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60abfbeb0f', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_65ddf62dd9', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_664aecfa4c', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7070cfbbdd', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7764eb9bbd', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b74bbc500a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c95c89b312', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_cd936e8563', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d766d7a8b3', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dbcdc8c839', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_dd9ef30ddd', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_e13d2dea57']`
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
- selected_candidate_count: `40`
- arm_count: `120`
- persisted_candidate_count: `40`
- persisted_arm_count: `120`
- missing: `[]`
- interpretation: `bottom_rebound source candidates were selected, armed, and persisted for label/EV handoff`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-07-14-8656b2573d57`
- source_hash: `8656b2573d57168f9c7c7415d7ce1fce6327e99a54a6236877f6c30b0d67e70e`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-07-14-72ad5e89afd0`
- previous_source_hash: `72ad5e89afd0d4ca71bb9b51b38b204de7856bcbc502dab6af35621928431f10`
- new_order_ids: `['order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9b786d75', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e5a75acf', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b59a2a69', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_40d1ca2c', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_40d1ca2c', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c09d7013', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b59a2a69', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fdb6ea3b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_13fbc66b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_f22492ef', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_8691c622']`
- removed_order_ids: `['order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_93cef898', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c09d7013', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d3af2240', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0acf4aba', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b7bc1628', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a7310af5', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b59a2a69', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_19ef6407', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_4c40c68d', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fdb6ea3b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_13fbc66b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a7310af5', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a7310af5', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9cb11ea2', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9cb11ea2', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_d3af2240', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_a9226f48', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_40d1ca2c']`
- decision_changed_order_ids: `[]`
