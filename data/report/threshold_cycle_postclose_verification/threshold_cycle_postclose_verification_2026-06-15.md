# Threshold Cycle Postclose Verification - 2026-06-15

- status: `fail`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-06-15 max_iterations=80 started_at=2026-06-15T15:45:01+0900`
- latest_done_marker: `[DONE] threshold-cycle postclose target_date=2026-06-15 ai_correction_provider=openai panic_sell_defense=true panic_buying=true market_panic_breadth=true scalp_sim_ai_deferred_review=true pipeline_event_verbosity=true observation_source_quality_audit=true codebase_performance_workorder=true pattern_lab_currentness_audit=true pattern_lab_ai_review=true time_window_regime_counterfactual=true producer_gap_discovery=true stage_hook_workorder_discovery=true stage_hook_runtime_scaffold=true pattern_lab_propagation_audit=true scalp_sim_overnight=true scalp_entry_adm=true institutional_flow_context=true microstructure_reaction_context=true lifecycle_decision_matrix=true lifecycle_ai_context=true ldm_hypothesis_parent_refinement=true lifecycle_bucket_discovery=true lifecycle_bucket_windows=true lifecycle_bucket_window_list=rolling5d,rolling10d,mtd lifecycle_bucket_promotion_window=mtd force_lifecycle_bucket_windows=false force_deep_audits=false force_workorder_branch=false runtime_apply_bridge=true scalp_sim_auto_approval_control_tower=true latency_classifier_recommendation=true tuning_performance_control_tower=true swing_lifecycle=true swing_strategy_discovery=true swing_lifecycle_matrix=true swing_lifecycle_bucket_discovery=true swing_ai_review_provider=openai swing_lifecycle_bucket_discovery_ai_provider=openai pattern_lab_ai_review_provider=openai producer_gap_discovery_ai_provider=openai stage_hook_workorder_discovery_ai_provider=openai pattern_labs=true deepseek_swing_lab=true code_improvement_workorder=true daily_ev=true runtime_approval_summary=true runtime_apply_gap_audit=true key_lineage_ledger=true conversion_lane=true next_stage2_checklist=true finished_at=2026-06-15T16:25:21+0900`
- predecessor_status: `fail`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['active_sim_priority_handoff_missing', 'scale_in_policy_contract_missing']`

## Execution Profile
- profile_status: `full_profile`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `latest DONE marker used full/default stage profile`
- missing_required_artifacts: `[]`
- missing_downstream_links: `[]`
- stale_downstream_links: `['threshold_cycle_ev_stale_before_code_improvement_workorder', 'runtime_approval_summary_stale_before_threshold_cycle_ev']`
- runtime_apply_gap_issues: `['runtime_apply_gap_audit_stale_before_threshold_preopen_apply', 'scale_in_policy_contract_missing']`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `pass_handoff_closed`
  - 근거: `{'status': 'pass', 'handoff_status': 'pass', 'root_cause_closure_status': 'closed', 'root_cause_open_reasons': [], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': [], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 0, 'submit_drought_refresh_applied_count': 0, 'submit_drought_latency_pass_recovered_count': 0, 'submit_drought_unknown_latency_reason_count': 0, 'ldm_submit_real_submitted_row_count': 9, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `No new implementation from this warning pass; continue postclose attribution and submit blocker tracking.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `source_quality_followup_required`
  - 근거: `{'status': 'warning', 'warnings': ['unknown_bucket_source_quality_gap'], 'affected_rows': 26, 'affected_rate': 0.0227, 'dimension_counts': {'score_bucket': 2, 'risk_context_bucket': 24, 'price_resolution_bucket': 15}, 'unknown_root_cause_counts': {'score_bucket:source_score_missing': 2, 'risk_context_bucket:risk_context_source_missing': 24, 'price_resolution_bucket:price_context_source_missing': 15}, 'stage_counts': {'scalp_sim_pre_submit_liquidity_guard_unknown': 2, 'latency_block': 18, 'blocked_ai_score': 117, 'scalp_sim_pre_submit_liquidity_guard_would_block': 75, 'pre_submit_liquidity_guard_block': 14, 'order_bundle_submitted': 9, 'scalp_sim_sell_order_assumed_filled': 15}, 'recommended_route': 'source_quality_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'-': 292, 'matched_prior_bucket': 811, 'new_or_unseen_token_vs_prior_adm': 41}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `warning_review_required`
  - 근거: `{'currentness_status': 'pass', 'currentness_fail_count': 0, 'ai_review_status': 'warning', 'ai_review_workorder_count': 4, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 481, 'lifecycle_flow_sim_probe_candidate': 6, 'sim_auto_approved': 5, 'entry_only_sim_auto_approved': 7, 'entry_only_source_candidate': 1}, 'source_bucket_kind_counts': {'source_only_observation': 417, 'taxonomy_provenance_gap': 64, 'lifecycle_flow_sim_probe_policy': 6, 'sim_auto_policy': 5, 'entry_only_sim_policy': 7, 'entry_only_source_candidate': 1}, 'runtime_gap_categories': {'code_patch_required': 10, 'runtime_blocked_contract_gap': 24, 'sim_auto_approved': 23, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 49, 'source_quality_blocker': 516, 'tier2_fail_closed_source_only': 12}, 'source_contract_status': 'warning', 'source_contract_change_count': 17, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 44, 'bridge_blocker_ledger_count': 200, 'runtime_uptake_rate_pct': 0.0, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `pass`
- retry_queue_count: `0`
- codex_directive_count: `1`
- summary: `{'actionable_unknown_gap_count': 0, 'ai_review_retry_pending': False, 'ai_review_status': 'parsed', 'bridge_blocker_ledger_count': 200, 'candidate_count': 635, 'codex_directive_count': 1, 'conversion_blocker_rank_count': 200, 'critical_failure_count': 0, 'derived_review_category_counts': {'code_patch_required': 10, 'runtime_blocked_contract_gap': 24, 'sim_auto_approved': 23, 'source_only_explicit_exclusion': 1, 'source_only_keep_collecting': 49, 'source_quality_blocker': 516, 'tier2_fail_closed_source_only': 12}, 'positive_edge_source_quality_pass_count': 44, 'quiet_gap_codex_directive_count': 0, 'quiet_gap_count': 400, 'quiet_gap_rollup_count': 400, 'retry_queue_count': 0, 'runtime_uptake_rate_pct': 0.0, 'source_dimension_gap_count': 64, 'status': 'pass'}`

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
- bucket_count ev/runtime/expected: `36` / `36` / `36`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Exit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `54` / `54` / `54`
- workorder_count ev/runtime/expected: `10` / `10` / `10`
- missing: `[]`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `17796`
- complete_flow_count: `79`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `79`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `17717`
- complete_flow_rate: `0.0044`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_holding`
- missing: `[]`

## AI Correction
- status: `pass`
- ai_status: `parsed`
- provider_status: `{'provider': 'openai', 'status': 'success', 'new_provider_call': True, 'key_name': 'OPENAI_API_KEY', 'attempt_index': 1, 'model_index': 1, 'configured_key_count': 2, 'attempted_key_count': 1, 'attempted_keys': 1, 'attempted_key_names': ['OPENAI_API_KEY'], 'configured_model_count': 3, 'attempted_model_count': 1, 'attempted_models': ['gpt-5.5'], 'configured_models': ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini'], 'model': 'gpt-5.5', 'schema_name': 'threshold_ai_correction_v1', 'reasoning_effort': 'high', 'prompt_chars': 108148, 'input_context_chars': 106828, 'input_context_hash': 'e9d816928c08a98e17471545f5294120ad904dd174afab0fa6d2392bc3faf025', 'elapsed_ms': 166712, 'output_chars': 11982, 'input_tokens': 31004, 'output_tokens': 9081, 'total_tokens': 40085, 'estimated_cost': None, 'estimated_cost_usd': None, 'cost_estimate_status': 'missing_price_contract'}`
- blocking_runtime_candidate_families: `['bad_entry_refined_canary', 'holding_exit_decision_matrix_advisory', 'holding_flow_ofi_smoothing', 'lifecycle_decision_matrix_runtime', 'protect_trailing_smoothing', 'score65_74_recovery_probe', 'soft_stop_whipsaw_confirmation']`
- parse_warnings: `[]`
- interpretation: `AI correction parsed successfully`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `15`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `pass`
- expected_candidate_ids: `['entry_bucket_10', 'entry_bucket_11', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_15', 'entry_bucket_16', 'entry_bucket_7', 'entry_bucket_8', 'entry_bucket_9']`
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
- policy_contract_status: `fail`
- policy_contract_missing: `['scale_in_policy_explicit_exclusion_missing', 'scale_in_policy_exclusion_reason_missing', 'scale_in_policy_source_link_missing', 'scale_in_policy_reopen_conditions_missing', 'scale_in_policy_runtime_gap_contract_not_closed']`
- policy_contract_interpretation: `Scale-in policy contract is not closed with source link, exclusion reason, and reopen trigger.`

## Overnight Bucket Handoff
- attribution_present: `True`
- source_present: `True`
- status: `pass`
- expected_candidate_ids: `['overnight_bucket_11', 'overnight_bucket_12', 'overnight_bucket_13', 'overnight_bucket_3', 'overnight_bucket_4', 'overnight_bucket_5', 'overnight_bucket_6', 'overnight_bucket_7', 'overnight_bucket_8']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- interpretation: `LDM overnight bucket candidates and workorders propagated to threshold EV, runtime summary, and code workorder.`

## Lifecycle Bucket Discovery Handoff
- status: `pass`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:chosen_action:wait_requote', 'entry:combo_entry_spot:score_score_60_62_source_scalp_entry_action_decision_snapshot_stale_fresh_liquidity_liquidity_hi', 'entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_ov', 'entry:combo_entry_spot:score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_high_over', 'entry:exit_rule:exit_unknown', 'entry:exit_rule:scalp_hard_stop_pct', 'entry:liquidity_bucket:liquidity_high', 'entry:overbought_bucket:overbought_normal', 'entry:score_band:score_66_69', 'entry:score_band:score_70p', 'entry:source_stage:wait6579_ev_cohort', 'entry:strength_bucket:strong_strength_momentum', 'entry:strength_bucket:weak_strength_momentum', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_fresh_liquidity_liquidity', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_bottoming_entry_allowed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_fresh_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_latency_block_revalidation_block_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_source_scalp_sim_pre_submit_liquidity_gua', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
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
- derived input/consumed: `4` / `4`
- derived_contract_drift_recompute_consumed: `True`
- closure_counts: `{'new_parent_candidate_created': 4}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 10678, 'recomputable_match_count': 10678, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_711caa66c89b3f51', 'ldm_hypothesis_92dfecb5a05caa64', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 0}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_beca38381060932e', 'ldm_refinement_eae97e493a708901', 'ldm_refinement_0d537f5033137f00']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `fail`
- active_seed_ids: `['active_seed_03c539e6527cdda2', 'active_seed_0747f150d4c2eab8', 'active_seed_136f942c5ddd1131', 'active_seed_5a2bc352f93a2417', 'active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83']`
- observed_seed_ids: `['active_seed_03c539e6527cdda2']`
- missing: `['active_sim_priority_producer_catalog_key_mismatch']`
- warnings: `['swing_active_arm_priority_runtime_observation_missing']`
- match_absence_diagnosis: `catalog_or_preopen_handoff_gap`
- match_absence_reason: `active_sim_priority_producer_catalog_key_mismatch`
- candidate_prefix_count: `10678`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 7705), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 2027), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 705), ('{"entry_score_parent": "score_extreme_confirmation", "entry_source_parent": "entry_source_wait6579"}', 144), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 97)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 34}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 36}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 41}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `pass`
- expected_candidate_ids: `['swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_26ca74e077', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_310f349c63', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_387f622ebb', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_56e6380928', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_60c4c4c8cf', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_6e73fea6f5', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7480cc41ef', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7764eb9bbd', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_7e0794e748', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_8070f782ab', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b0984ff4fa', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_b74bbc500a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_c515f99b98', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ccc3dfa9db', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d105b725f2', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_d955279f8b', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_da5b17ed0a', 'swing_ldm_lifecycle_flow_combo_swing_lifecycle_flow_entry_swing_entry_entry_bucket_attribution_swing_strategy_discovery_s_ece5318efb']`
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
- selected_candidate_count: `25`
- arm_count: `75`
- persisted_candidate_count: `25`
- persisted_arm_count: `75`
- missing: `[]`
- interpretation: `bottom_rebound source candidates were selected, armed, and persisted for label/EV handoff`

## Runtime Gap Provenance
- active_gap_count: `0`
- raw_preserved: `None`
- gap_affected_handoff_count: `0`

## Workorder Snapshot
- generation_id: `2026-06-15-061875c25da5`
- source_hash: `061875c25da5537d9520db3efcf9fd097f5747e13cb0e2a24c7c63912e295c64`
- snapshot_status: `source_changed_with_lineage`
- previous_generation_id: `2026-06-15-a3c988d916c6`
- previous_source_hash: `a3c988d916c623f7891e4b77023a2120aed0ea5d20f09707470d5c1715441b56`
- new_order_ids: `[]`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
