# Threshold Cycle Postclose Verification - 2026-09-04

- status: `warning`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-09-04 max_iterations=320 recovery_reuse=false started_at=2026-09-04T20:10:02+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-09-04 ai_correction_provider=openai panic_sell_defense=true market_panic_breadth=true pipeline_event_verbosity=true limit_down_watch_report=true observation_source_quality_audit=true scanner_lookup_attention_tuning=true opening_rotation_profile_tuning=retired ai_decision_quality_daily_materialization=true main_ai_quality_r0_r3=true main_ai_prompt_optimizer=true main_ai_prompt_consumer=true main_ai_quality_provider_replay=true ai_decision_action_outcome_calibration=true codebase_performance_workorder=false pattern_lab_currentness_audit=true pattern_lab_ai_review=true time_window_regime_counterfactual=false producer_gap_discovery=false stage_hook_workorder_discovery=false stage_hook_runtime_scaffold=false pattern_lab_propagation_audit=true scalp_sim_overnight=true scalp_entry_adm=true entry_split_order_plan=true scale_in_split_order_plan=true entry_ai_gate_backtest=true rising_missed_intraday_feedback_postclose=true rising_missed_scout_workorder=true scalping_pyramid_intraday_feedback_postclose=true scalping_pyramid_quality_calibration=true scalping_avg_down_recovery_calibration=true rising_missed_classifier_prior=true samsung_machine_entry_tuning=true low_price_two_leg_tuning=true low_price_two_leg_candidate_recommendation=true machine_microstructure_attribution=false one_share_threshold_opportunity=true one_share_threshold_opportunity_ai_provider=openai institutional_flow_context=true microstructure_reaction_context=true lifecycle_decision_matrix=true lifecycle_ai_context=true ldm_hypothesis_parent_refinement=true lifecycle_bucket_discovery=true lifecycle_bucket_windows=true lifecycle_bucket_window_list=rolling5d,rolling10d,mtd lifecycle_bucket_promotion_window=mtd force_lifecycle_bucket_windows=false force_deep_audits=false force_workorder_branch=false runtime_apply_bridge=true scalp_sim_auto_approval_control_tower=true latency_classifier_recommendation=true tuning_performance_control_tower=true swing_lifecycle=false swing_strategy_discovery=false swing_lifecycle_matrix=false swing_lifecycle_bucket_discovery=false swing_ai_review_provider=openai swing_lifecycle_bucket_discovery_ai_provider=openai pattern_lab_ai_review_provider=openai producer_gap_discovery_ai_provider=openai stage_hook_workorder_discovery_ai_provider=openai pattern_labs=true deepseek_swing_lab=false code_improvement_workorder=true daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true key_lineage_ledger=true conversion_lane=true next_stage2_checklist=true finished_at=2026-09-04T21:14:12+0900`
- predecessor_status: `pass`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `[]`

## Execution Profile
- profile_status: `recovered_partial_profile`
- disabled_stage_flags: `['swing_lifecycle', 'swing_strategy_discovery', 'swing_lifecycle_matrix', 'swing_lifecycle_bucket_discovery', 'deepseek_swing_lab', 'time_window_regime_counterfactual', 'producer_gap_discovery', 'stage_hook_workorder_discovery', 'stage_hook_runtime_scaffold']`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker was produced by controller recovery action `None` with selected heavy stages disabled; the prior full-run execution contract is inherited and same-date artifacts are still validated separately`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`
- smoothing_source_only_path_journal: `pass`
- smoothing_source_only_path_journal_issues: `[]`
- smoothing_source_only_rolling_decision: `pass`
- scanner_lookup_attention_status: `pass`
- scanner_lookup_attention_promotion_state: `source_quality_blocked`
- scanner_lookup_attention_allowed_runtime_apply: `False`

## Machine Entry Timing Waiting Classification
- contract_status: `pass`
- sample_floor_state: `source_quality_blocked`
- waiting_resolution_status: `terminal_source_date_quarantine`
- shortage_class: `structural_population_exhaustion`
- shortage_id: `machine_entry_timing:all_exact_scopes:entry_confirmation_delay`
- next_action: `quarantine_exact_source_date_and_verify_next_runtime_receipt`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_handoff_closed`
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['ENTRY_AI_AUTHORITY_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 13, 'submit_drought_refresh_applied_count': 13, 'submit_drought_latency_pass_recovered_count': 2, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 3, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `pass_no_unknown_bucket_warning`
  - 근거: `{'status': 'pass', 'warnings': [], 'affected_rows': 1, 'affected_rate': 0.0019, 'dimension_counts': {'risk_context_bucket': 1, 'price_resolution_bucket': 1}, 'unknown_root_cause_counts': {'risk_context_bucket:post_submit_or_exit_not_required': 1, 'price_resolution_bucket:post_submit_or_exit_not_required': 1}, 'stage_counts': {'latency_block': 36, 'scalp_entry_action_decision_snapshot': 202, 'blocked_ai_score': 33, 'entry_submit_revalidation_block': 6, 'order_bundle_submitted': 3, 'scalp_sim_entry_ai_price_skip_order': 2, 'scalp_sim_pre_submit_overbought_guard_would_block': 1, 'scalp_sim_sell_order_assumed_filled': 1}, 'recommended_route': 'classified_not_applicable_no_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'matched_prior_bucket': 379, 'new_or_unseen_token_vs_prior_adm': 159}}`
  - 다음 액션: `No actionable unknown bucket remains. Preserve the classified non-actionable cohort and reopen only if a required entry-stage source field becomes unknown.`
- P3 `pattern_lab_warning` 판정: `warning_review_required`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'warning', 'ai_review_workorder_count': 2, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 272, 'entry_only_sim_auto_approved': 1, 'entry_only_source_candidate': 7, 'sim_auto_approved': 1}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 29, 'source_only_observation': 243, 'entry_only_sim_policy': 1, 'entry_only_source_candidate': 7, 'sim_auto_policy': 1}, 'runtime_gap_categories': {'code_patch_required': 1, 'runtime_blocked_contract_gap': 11, 'sim_auto_approved': 1, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 2, 'source_quality_blocker': 2}, 'source_contract_status': 'pass', 'source_contract_change_count': 0, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 2, 'bridge_blocker_ledger_count': 18, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': []}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 18, 'candidate_count': 18, 'codex_directive_count': 0, 'conversion_blocker_rank_count': 17, 'critical_failure_count': 0, 'derived_review_category_counts': {'code_patch_required': 1, 'runtime_blocked_contract_gap': 11, 'sim_auto_approved': 1, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 2, 'source_quality_blocker': 2}, 'positive_edge_source_quality_pass_count': 2, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 233, 'quiet_gap_rollup_count': 233, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 26, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `14` / `14` / `14`
- workorder_count ev/runtime/expected: `0` / `0` / `0`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `21` / `21` / `21`
- workorder_count ev/runtime/expected: `8` / `8` / `8`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `642`
- complete_flow_count: `5`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `5`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `637`
- complete_flow_rate: `0.0078`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- ai_coverage_status: `complete`
- family_coverage: reviewed=`20` / expected=`20`
- missing_families: `[]`
- duplicate_families: `[]`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 135383, 'input_context_chars': 133921, 'input_context_hash': '5417dc7204f829ec08b7a7365a5a72fcf148b3abbb8e31e23c5b819f19e8497c', 'elapsed_ms': 84614, 'output_chars': 15605, 'input_tokens': 37635, 'output_tokens': 7174, 'total_tokens': 44809, 'estimated_cost': 0.0, 'estimated_cost_usd': 0.0, 'cost_estimate_status': 'operator_zero_cost_default', 'coverage_repair': {'status': 'not_needed', 'initial_ai_status': 'parsed', 'initial_parse_warnings': [], 'initial_missing_families': [], 'initial_duplicate_families': [], 'initial_unexpected_families': [], 'repair_shard_count': 0, 'repair_shards': [], 'remaining_missing_families': [], 'additional_provider_usage': {}, 'aggregate_provider_usage': {'input_tokens': 37635, 'output_tokens': 7174, 'total_tokens': 44809, 'elapsed_ms': 84614, 'estimated_cost': 0.0, 'estimated_cost_usd': 0.0}, 'runtime_change': False}, 'aggregate_input_tokens': 37635, 'aggregate_output_tokens': 7174, 'aggregate_total_tokens': 44809, 'aggregate_elapsed_ms': 84614, 'aggregate_estimated_cost': 0.0, 'aggregate_estimated_cost_usd': 0.0}`
- blocking_runtime_candidate_families: `['holding_exit_decision_matrix_advisory', 'lifecycle_decision_matrix_runtime', 'score65_74_recovery_probe']`
- incomplete_runtime_candidate_families: `[]`
- parse_warnings: `[]`
- interpretation: `AI correction parsed with exactly one review for every candidate family`

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
- source_contract_status: `pass`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:combo_entry_spot:score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:liquidity_bucket:liquidity_high', 'entry:stage_policy:entry_weighted_adm_v1', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
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
- derived input/consumed: `4` / `4`
- derived_contract_drift_recompute_consumed: `True`
- closure_counts: `{'new_parent_candidate_created': 2, 'rare_observation_only_budget_capped': 1, 'rejected_as_fragile': 1}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 0, 'recomputable_match_count': 0, 'recomputable_hypothesis_ids': [], 'runtime_matched_event_count': 0}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_fc086bd62f97a8ce', 'ldm_refinement_93bd091abca52ce8', 'ldm_refinement_17c30efd598b9293', 'ldm_refinement_b97eb32d0db6cec1']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `pass`
- active_seed_ids: `['rising_missed_prior_e65574639530054b', 'rising_missed_prior_f136f8679a996252']`
- observed_seed_ids: `[]`
- missing: `[]`
- warnings: `[]`
- match_absence_diagnosis: `not_applicable`
- match_absence_reason: `active_priority_observed_or_no_active_priority`
- candidate_prefix_count: `487`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 215), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 196), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 75), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 1)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 36, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 45, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 33, 'window_role': 'promotion_confirmation'}}`
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
- generation_id: `2026-09-04-1f7ce6aae705`
- source_hash: `dcb090e16d60c4bbf4cf6457e71166cc9ed2c2568b27d78a8578361c2cd3e0a5`
- snapshot_status: `same_snapshot_replay`
- previous_generation_id: `2026-09-04-1f7ce6aae705`
- previous_source_hash: `dcb090e16d60c4bbf4cf6457e71166cc9ed2c2568b27d78a8578361c2cd3e0a5`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
