# Threshold Cycle Postclose Verification - 2026-06-12

- status: `fail`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-06-12 max_iterations=80 started_at=2026-06-12T15:45:01+0900`
- latest_done_marker: `-`
- predecessor_status: `fail`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['active_sim_priority_handoff_missing', 'ldm_entry_bucket_handoff_missing', 'ldm_overnight_bucket_handoff_missing', 'lifecycle_bucket_discovery_handoff_missing', 'postclose_fail_marker_present', 'scale_in_policy_contract_missing']`

## Execution Profile
- profile_status: `done_marker_missing`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest START marker has no matching DONE marker`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `['threshold_cycle_ev_stale_before_code_improvement_workorder', 'threshold_cycle_ev_stale_before_pattern_lab_currentness_audit']`
- runtime_apply_gap_issues: `['runtime_apply_gap_audit_stale_before_runtime_apply_bridge', 'runtime_apply_gap_audit_stale_before_threshold_preopen_apply', 'scale_in_policy_contract_missing']`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_handoff_closed`
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 0, 'submit_drought_refresh_applied_count': 0, 'submit_drought_latency_pass_recovered_count': 0, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 17, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['unknown_bucket_source_quality_gap'], 'affected_rows': 334, 'affected_rate': 0.2807, 'dimension_counts': {'score_bucket': 334, 'risk_context_bucket': 36, 'price_resolution_bucket': 19}, 'unknown_root_cause_counts': {'score_bucket:source_score_missing': 334, 'risk_context_bucket:risk_context_source_missing': 36, 'price_resolution_bucket:price_context_source_missing': 19}, 'stage_counts': {'latency_block': 27, 'scalp_sim_pre_submit_liquidity_guard_would_block': 247, 'blocked_ai_score': 88, 'pre_submit_liquidity_guard_block': 18, 'order_bundle_submitted': 17, 'scalp_sim_pre_submit_liquidity_guard_unknown': 27, 'scalp_sim_pre_submit_overbought_guard_would_block': 4, 'pre_submit_overbought_pullback_guard_block': 2, 'scalp_sim_sell_order_assumed_filled': 19}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 1013, 'new_or_unseen_token_vs_prior_adm': 177}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `warning_review_required`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'warning', 'ai_review_workorder_count': 6, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 485, 'lifecycle_flow_sim_probe_candidate': 5, 'entry_only_sim_auto_approved': 10}, 'source_bucket_kind_counts': {'source_only_observation': 416, 'taxonomy_provenance_gap': 69, 'lifecycle_flow_sim_probe_policy': 5, 'entry_only_sim_policy': 10}, 'runtime_gap_categories': {'code_patch_required': 13, 'runtime_blocked_contract_gap': 24, 'sim_auto_approved': 46, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 56, 'source_quality_blocker': 535, 'tier2_fail_closed_source_only': 8}, 'source_contract_status': 'warning', 'source_contract_change_count': 16, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 29, 'bridge_blocker_ledger_count': 200, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `1`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 683, 'codex_directive_count': 1, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'code_patch_required': 13, 'runtime_blocked_contract_gap': 24, 'sim_auto_approved': 46, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 56, 'source_quality_blocker': 535, 'tier2_fail_closed_source_only': 8}, 'positive_edge_source_quality_pass_count': 29, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 284, 'quiet_gap_rollup_count': 284, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 72, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `38` / `38` / `38`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `49` / `49` / `49`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `16902`
- complete_flow_count: `94`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `94`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `16808`
- complete_flow_rate: `0.0056`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 109193, 'input_context_chars': 107873, 'input_context_hash': '97335284d4d0a90cdc20d7bccd899629ca50b4f9ee4eed69a7fa9f30f20d946e', 'elapsed_ms': 141585, 'output_chars': 12313, 'input_tokens': 31232, 'output_tokens': 9523, 'total_tokens': 40755, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'holding_flow_ofi_smoothing', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `19`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `fail`
- expected_candidate_ids: `['entry_bucket_11', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_15', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_9']`
- missing_ev_candidate_ids: `['entry_bucket_11', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_15', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_9']`
- missing_runtime_summary_candidate_ids: `['entry_bucket_11', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_15', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_9']`
- missing_workorder_order_ids: `['order_lifecycle_entry_bucket_overbought_bucket_overbought_normal', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_ok', 'order_lifecycle_entry_bucket_score_band_score_60_62', 'order_lifecycle_entry_bucket_score_band_score_lt60']`
- interpretation: `LDM entry bucket output was generated but one or more downstream consumers dropped it.`

## Scale-In Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM scale-in bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`
- policy_contract_status: `fail`
- policy_contract_missing: `['scale_in_policy_explicit_exclusion_missing', 'scale_in_policy_exclusion_reason_missing', 'scale_in_policy_source_link_missing', 'scale_in_policy_reopen_conditions_missing', 'scale_in_policy_runtime_gap_contract_not_closed']`
- policy_contract_interpretation: `Scale-in policy contract is not closed with source link, exclusion reason, and reopen trigger.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `fail`
- expected_candidate_ids: `['overnight_bucket_1', 'overnight_bucket_10', 'overnight_bucket_11', 'overnight_bucket_2', 'overnight_bucket_3', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_8', 'overnight_bucket_9']`
- missing_ev_candidate_ids: `['overnight_bucket_1', 'overnight_bucket_10', 'overnight_bucket_11', 'overnight_bucket_2', 'overnight_bucket_3', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_8', 'overnight_bucket_9']`
- missing_runtime_summary_candidate_ids: `['overnight_bucket_1', 'overnight_bucket_10', 'overnight_bucket_11', 'overnight_bucket_2', 'overnight_bucket_3', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_8', 'overnight_bucket_9']`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket output was generated but one or more downstream consumers dropped it.`

## Lifecycle Bucket Discovery Handoff
- status: `fail`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:chosen_action:no_buy_ai', 'entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hi', 'entry:combo_entry_spot:score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hig', 'entry:exit_rule:scalp_hard_stop_pct', 'entry:exit_rule:scalp_soft_stop_pct', 'entry:liquidity_bucket:liquidity_high', 'entry:overbought_bucket:overbought_normal', 'entry:overbought_bucket:overbought_ok', 'entry:source_stage:scalp_entry_action_decision_snapshot', 'entry:strength_bucket:weak_strength_momentum', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_high_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_watch_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_overbought_gu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `['entry:strength_bucket:weak_strength_momentum']`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery produced surfaced candidates that downstream consumers dropped`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `3` / `3`
- derived input/consumed: `3` / `3`
- derived_contract_drift_recompute_consumed: `True`
- closure_counts: `{'new_parent_candidate_created': 1, 'rare_observation_only_budget_capped': 2}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 1337, 'recomputable_match_count': 1337, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_92dfecb5a05caa64', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 0}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_8df25ffe7ff6b944', 'ldm_refinement_dda62c883299b94c', 'ldm_refinement_8a49a49c35b8db99']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `fail`
- active_seed_ids: `['active_seed_03c539e6527cdda2', 'active_seed_136f942c5ddd1131', 'active_seed_5fbf3e3baf24631e', 'active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83']`
- observed_seed_ids: `['active_seed_5a2bc352f93a2417', 'active_seed_b99a2dea7aac2a83', 'active_seed_d263354d5e66d645']`
- missing: `['active_sim_priority_producer_catalog_key_mismatch', 'active_sim_priority_preopen_handoff_missing']`
- warnings: `['swing_active_arm_priority_runtime_observation_missing']`
- match_absence_diagnosis: `catalog_or_preopen_handoff_gap`
- match_absence_reason: `active_sim_priority_preopen_handoff_missing,active_sim_priority_producer_catalog_key_mismatch`
- candidate_prefix_count: `1337`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 652), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 623), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 62)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 39}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 40}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 40}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `['swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_4119f0435d', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7d92990310', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_9694893e9a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a']`
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
- selected_candidate_count: `32`
- arm_count: `96`
- persisted_candidate_count: `32`
- persisted_arm_count: `96`
- missing: `[]`
- interpretation: `bottom_rebound source candidates were selected, armed, and persisted for label/EV handoff`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-06-12-40732e220815`
- source_hash: `40732e220815dede266faf83f75930a2115c82f2b7d65b42d16630171e695fe2`
- snapshot_status: `same_snapshot_replay`
- previous_generation_id: `2026-06-12-40732e220815`
- previous_source_hash: `40732e220815dede266faf83f75930a2115c82f2b7d65b42d16630171e695fe2`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
