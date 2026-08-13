# Threshold Cycle Postclose Verification - 2026-08-13

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-08-13 max_iterations=320 recovery_reuse=false started_at=2026-08-13T20:10:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-08-13 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false deepseek_swing_lab=false swing_lifecycle=false swing_lifecycle_bucket_discovery=false swing_lifecycle_matrix=false swing_strategy_discovery=false finished_at=2026-08-13T21:25:21+0900`
- predecessor_status: `pass`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `[]`

## Execution Profile
- profile_status: `recovered_partial_profile`
- disabled_stage_flags: `['swing_lifecycle', 'swing_strategy_discovery', 'swing_lifecycle_matrix', 'swing_lifecycle_bucket_discovery', 'deepseek_swing_lab']`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker was produced by controller recovery action `tail_repair_done_reconciliation` with selected heavy stages disabled; the prior full-run execution contract is inherited and same-date artifacts are still validated separately`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`
- smoothing_source_only_path_journal: `pass`
- smoothing_source_only_path_journal_issues: `[]`
- smoothing_source_only_rolling_decision: `pass`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_handoff_closed`
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 67, 'submit_drought_refresh_applied_count': 30, 'submit_drought_latency_pass_recovered_count': 8, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 5, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'sim_post_sell_outcome_source_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 4, 'affected_rate': 0.0071, 'dimension_counts': {'score_bucket': 1, 'risk_context_bucket': 3, 'price_resolution_bucket': 3}, 'unknown_root_cause_counts': {'score_bucket:source_score_missing': 1, 'risk_context_bucket:post_submit_or_exit_not_required': 3, 'price_resolution_bucket:post_submit_or_exit_not_required': 3}, 'stage_counts': {'scalp_entry_action_decision_snapshot': 182, 'latency_block': 30, 'blocked_ai_score': 35, 'scalp_sim_pre_submit_liquidity_guard_would_block': 9, 'scalp_sim_entry_ai_price_skip_order': 21, 'order_bundle_submitted': 5, 'pre_submit_liquidity_guard_block': 1, 'entry_submit_revalidation_block': 1, 'scalp_sim_sell_order_assumed_filled': 3}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'new_or_unseen_token_vs_prior_adm': 146, 'matched_prior_bucket': 414}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `pass_no_current_handoff_workorder`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'pass', 'ai_review_workorder_count': 0, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 376, 'lifecycle_flow_sim_probe_candidate': 3}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 32, 'lifecycle_flow_sim_probe_policy': 3, 'source_only_observation': 344}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 13, 'source_only_explicit_exclusion': 2}, 'source_contract_status': 'pass', 'source_contract_change_count': 0, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 0, 'bridge_blocker_ledger_count': 15, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': []}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'not_required', 'bridge_blocker_ledger_count': 15, 'candidate_count': 15, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 15, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 13, 'source_only_explicit_exclusion': 2}, 'positive_edge_source_quality_pass_count': 0, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 328, 'quiet_gap_rollup_count': 328, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 27, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `21` / `21` / `21`
- workorder_count ev/runtime/expected: `8` / `8` / `8`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `28` / `28` / `28`
- workorder_count ev/runtime/expected: `5` / `5` / `5`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `2395`
- complete_flow_count: `7`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `7`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `2388`
- complete_flow_rate: `0.0029`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 118514, 'input_context_chars': 117104, 'input_context_hash': 'bb733787f3829853a18c1f5e6667029136012926ba9df31459d57978ce7edc67', 'elapsed_ms': 80161, 'output_chars': 13550, 'input_tokens': 34102, 'output_tokens': 7684, 'total_tokens': 41786, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'entry_split_order_plan', 'holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'score65_74_recovery_probe']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `3`
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
- source_contract_status: `pass`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_blocked_ai_score_stale_fresh_liquidity_liqui', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_entry_ai_price_skip_order_stale_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_entry_ai_price_skip_order_stale_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_entry_ai_price_skip_order_stale_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_ok_or_u', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
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
- derived input/consumed: `3` / `3`
- derived_contract_drift_recompute_consumed: `True`
- closure_counts: `{'new_parent_candidate_created': 3}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 0, 'recomputable_match_count': 0, 'recomputable_hypothesis_ids': [], 'runtime_matched_event_count': 0}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_83c40d07394c05ba', 'ldm_refinement_13c41c6a48798c3f', 'ldm_refinement_96e3238ec3087374']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `['active_seed_de26846dde62fe15']`
- observed_seed_ids: `['rising_missed_prior_f136f8679a996252']`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `134`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 100), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 17), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 17)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 33, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 43, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 45, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `disabled`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `None`
- ai_two_pass_review_status: `-`
- warnings: `[]`
- interpretation: `-`

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

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-08-13-a600b55fc106`
- source_hash: `a600b55fc106054aaa0ed8c17bb102f5c51f85ea043f5d3f79e2e09444f39e19`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-08-13-53c3eca28097`
- previous_source_hash: `53c3eca280973f774670a746db1caaa01cd8ee71c340ed802d509967e7007d64`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
