# Threshold Cycle Postclose Verification - 2026-08-11

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-08-11 max_iterations=320 recovery_reuse=false started_at=2026-08-11T20:10:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-08-11 recovery_action=tail_repair_done_reconciliation full_wrapper_rerun=false deepseek_swing_lab=false swing_lifecycle=false swing_lifecycle_bucket_discovery=false swing_lifecycle_matrix=false swing_strategy_discovery=false finished_at=2026-08-11T21:15:56+0900`
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
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 45, 'submit_drought_refresh_applied_count': 25, 'submit_drought_latency_pass_recovered_count': 1, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 0, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['joined_sample_below_sample_floor', 'sim_post_sell_outcome_source_below_sample_floor', 'unknown_bucket_source_quality_gap'], 'affected_rows': 1, 'affected_rate': 0.002, 'dimension_counts': {'risk_context_bucket': 1}, 'unknown_root_cause_counts': {'risk_context_bucket:source_field_missing': 1}, 'stage_counts': {'blocked_ai_score': 44, 'latency_block': 26, 'scalp_entry_action_decision_snapshot': 77, 'scalp_sim_entry_ai_price_skip_order': 31}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 357, 'new_or_unseen_token_vs_prior_adm': 138}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `warning_review_required`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'warning', 'ai_review_workorder_count': 1, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 228}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 26, 'source_only_observation': 202}, 'runtime_gap_categories': {'runtime_blocked_contract_gap': 10, 'source_only_explicit_exclusion': 2}, 'source_contract_status': 'pass', 'source_contract_change_count': 0, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 0, 'bridge_blocker_ledger_count': 12, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': []}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'not_required', 'bridge_blocker_ledger_count': 12, 'candidate_count': 12, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 12, 'critical_failure_count': 0, 'derived_review_category_counts': {'runtime_blocked_contract_gap': 10, 'source_only_explicit_exclusion': 2}, 'positive_edge_source_quality_pass_count': 0, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 189, 'quiet_gap_rollup_count': 189, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 21, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `7` / `7` / `7`
- workorder_count ev/runtime/expected: `3` / `3` / `3`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `16` / `16` / `16`
- workorder_count ev/runtime/expected: `1` / `1` / `1`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `146`
- complete_flow_count: `3`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `3`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `143`
- complete_flow_rate: `0.0205`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 115197, 'input_context_chars': 113787, 'input_context_hash': 'dbfbc6905f87426a4118fc51a4aba38afcb46d982848e35cdcce0a4ed65224f3', 'elapsed_ms': 96173, 'output_chars': 13500, 'input_tokens': 33161, 'output_tokens': 8461, 'total_tokens': 41622, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'entry_split_order_plan', 'holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'score65_74_recovery_probe']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `0`
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
- source_present: `False`
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
- expected_candidate_ids: `['lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_entry_ai_price_skip_order_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_entry_ai_price_skip_order_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `[]`
- interpretation: `lifecycle bucket discovery candidates propagated to bridge/runtime summary/workorder`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `4` / `4`
- derived input/consumed: `0` / `0`
- derived_contract_drift_recompute_consumed: `False`
- closure_counts: `{'new_parent_candidate_created': 4}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 56, 'recomputable_match_count': 56, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_711caa66c89b3f51', 'ldm_hypothesis_92dfecb5a05caa64', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 56}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_2e98b9bcd9356d65', 'ldm_refinement_d8301cd2cc6b560e', 'ldm_refinement_d168fa5014a605f4', 'ldm_refinement_20f99c6fa2f2312b']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `not_applicable`
- active_seed_ids: `[]`
- observed_seed_ids: `['active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83', 'rising_missed_prior_e65574639530054b', 'rising_missed_prior_f136f8679a996252']`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `56`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 33), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 13), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 7), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 3)]`

## Lifecycle Bucket Windows
- status: `warning`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'too_broad', 'parent_bucket_count': 28, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 37, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 37, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `['lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target']`

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
- generation_id: `2026-08-11-24b51f5b6416`
- source_hash: `24b51f5b64168e6e9481cdca1eb79fc4312c8f54f4b11b54aed8de56019c1777`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-08-11-ab802a6ba4d7`
- previous_source_hash: `ab802a6ba4d73fb7184efad620d9738e699a5a8ffa2d9af7696c56a9136e16ed`
- new_order_ids: `[]`
- removed_order_ids: `['order_pattern_lab_ai_review_lifecycle_decision_matrix_all_policy_entries_below_sample_floor']`
- decision_changed_order_ids: `[]`
