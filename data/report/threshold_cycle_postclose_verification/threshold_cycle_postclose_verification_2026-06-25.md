# Threshold Cycle Postclose Verification - 2026-06-25

- status: `fail`
- latest_start_marker: `[START] threshold-cycle postclose target_date=2026-06-25 max_iterations=80 started_at=2026-06-25T20:10:01+0900`
- latest_done_marker: `-`
- predecessor_status: `fail`
- predecessor_wait_count: `0`
- predecessor_timeout_count: `0`
- log_issues: `['active_sim_priority_handoff_missing', 'ldm_entry_bucket_handoff_missing', 'ldm_exit_bucket_handoff_missing', 'ldm_holding_bucket_handoff_missing', 'lifecycle_bucket_discovery_handoff_missing', 'scale_in_policy_contract_missing']`

## Execution Profile
- profile_status: `pending_done_marker`
- disabled_stage_flags: `[]`
- missing_required_flags: `[]`
- interpretation: `wrapper-internal verification passed required artifacts; final DONE marker is checked by a later health check`
- missing_required_artifacts: `['runtime_approval_summary', 'pattern_lab_currentness_audit', 'pattern_lab_propagation_audit', 'swing_daily_simulation', 'swing_lifecycle_audit', 'next_stage2_checklist']`
- missing_downstream_links: `['runtime_approval_summary_sources_ev', 'threshold_cycle_ev_sources_pattern_lab_currentness_audit', 'threshold_cycle_ev_sources_pattern_lab_propagation_audit', 'runtime_approval_summary_sources_scalp_entry_action_decision_matrix', 'runtime_approval_summary_sources_lifecycle_decision_matrix', 'runtime_approval_summary_sources_pattern_lab_propagation_audit']`
- stale_downstream_links: `[]`
- runtime_apply_gap_issues: `[]`

## Warning Follow-Up Summary
- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- P1 `submit_drought` 판정: `needs_followup`
  - 근거: `{'status': 'warning', 'handoff_status': 'pass', 'root_cause_closure_status': 'open', 'root_cause_open_reasons': ['unknown_latency_reason_present', 'unknown_latency_workorder_required', 'ldm_submit_quote_freshness_attribution_missing'], 'artifact_regeneration_required': False, 'critical': True, 'primary': 'SUBMIT_DROUGHT_CRITICAL', 'matches': ['PRICE_GUARD_DROUGHT', 'LATENCY_DROUGHT', 'UPSTREAM_AI_THRESHOLD', 'SUBMIT_DROUGHT_CRITICAL'], 'missing': ['ldm_submit_quote_freshness_attribution_missing', 'runtime_approval_summary_buy_funnel_sentinel_missing', 'runtime_approval_summary_entry_submit_drought_handoff_missing'], 'quote_freshness_attribution_inconsistent': False, 'submit_drought_refresh_attempted_count': 14, 'submit_drought_refresh_applied_count': 12, 'submit_drought_latency_pass_recovered_count': 6, 'submit_drought_unknown_latency_reason_count': 4, 'ldm_submit_real_submitted_row_count': 5, 'ldm_submit_missing_broker_order_key_count': 0, 'ldm_submit_missing_broker_order_key_rate': 0.0, 'ldm_submit_post_submit_provenance_join_gap': False, 'ldm_submit_post_submit_provenance_join_gap_raw': False, 'ldm_submit_bot_history_backfill_candidate_count': 0, 'ldm_submit_bot_history_backfill_full_coverage': False, 'ldm_submit_bot_history_exact_mapping_count': 0, 'ldm_submit_bot_history_exact_mapping_full_coverage': False, 'ldm_submit_post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows'}`
  - 다음 액션: `Restore missing workorder/LDM/EV/runtime-summary submit drought handoff.`
- P2 `scalp_entry_adm_unknown_bucket_source_quality_gap` 판정: `pass_no_unknown_bucket_warning`
  - 근거: `{'status': 'warning', 'warnings': ['ai_numeric_consistency_rows_excluded_from_aggregates'], 'affected_rows': 12, 'affected_rate': 0.0214, 'dimension_counts': {'risk_context_bucket': 12, 'price_resolution_bucket': 4}, 'unknown_root_cause_counts': {'risk_context_bucket:post_submit_or_exit_not_required': 12, 'price_resolution_bucket:post_submit_or_exit_not_required': 4}, 'stage_counts': {'scalp_sim_sell_order_assumed_filled': 7, 'blocked_ai_score': 53, 'scalp_sim_pre_submit_liquidity_guard_would_block': 29, 'pre_submit_liquidity_guard_block': 3, 'scalp_sim_pre_submit_overbought_guard_would_block': 1, 'order_bundle_submitted': 5}, 'recommended_route': 'classified_not_applicable_no_workorder', 'not_available_route': 'field_legitimately_unavailable_no_workorder', 'lookup_status_counts': {'new_or_unseen_token_vs_prior_adm': 99, 'matched_prior_bucket': 462}}`
  - 다음 액션: `Prioritize source score emission for score_bucket unknown rows, then risk_context/price_resolution source fields; keep not_available buckets as explicit non-workorder context unless they become required source fields.`
- P3 `pattern_lab_warning` 판정: `pass_no_current_handoff_workorder`
  - 근거: `{'currentness_status': '', 'currentness_fail_count': 0, 'ai_review_status': '', 'ai_review_workorder_count': 0, 'ai_review_warnings': []}`
  - 다음 액션: `No new pattern-lab implement_now item; keep pattern lab warning as source-only monitoring unless fresh currentness or AI review emits a concrete workorder.`
- P4 `live_auto_ready_zero_breakdown` 판정: `warning_explained_no_live_auto_ready`
  - 근거: `{'live_auto_apply_ready_count': 0, 'state_counts': {'source_only_keep_collecting': 480, 'lifecycle_flow_sim_probe_candidate': 5, 'sim_auto_approved': 5, 'entry_only_sim_auto_approved': 9, 'entry_only_source_candidate': 1}, 'source_bucket_kind_counts': {'taxonomy_provenance_gap': 50, 'source_only_observation': 430, 'lifecycle_flow_sim_probe_policy': 5, 'sim_auto_policy': 5, 'entry_only_sim_policy': 9, 'entry_only_source_candidate': 1}, 'runtime_gap_categories': {}, 'source_contract_status': 'warning', 'source_contract_change_count': 12, 'ai_two_pass_review_status': 'parsed', 'positive_edge_source_quality_pass_count': 0, 'bridge_blocker_ledger_count': 0, 'runtime_uptake_rate_pct': None, 'handoff_warnings': ['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']}`
  - 다음 액션: `Keep complete lifecycle promotion as the owner; close source-contract drift, source-quality blockers, and runtime_blocked_contract_gap buckets before expecting live-auto candidates.`

## Runtime Apply Gap Audit
- status: `missing`
- retry_queue_count: `0`
- codex_directive_count: `0`
- summary: `{}`

## BUY Funnel Submit Drought Handoff
- status: `warning`
- critical: `True`
- missing: `['ldm_submit_quote_freshness_attribution_missing', 'runtime_approval_summary_buy_funnel_sentinel_missing', 'runtime_approval_summary_entry_submit_drought_handoff_missing']`

## Submit Bucket Handoff
- status: `pass`
- attribution_present: `True`
- missing: `[]`

## Holding Bucket Handoff
- status: `fail`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `29` / `-1` / `29`
- workorder_count ev/runtime/expected: `10` / `-1` / `10`
- missing: `['runtime_approval_summary_holding_bucket_count_missing', 'runtime_approval_summary_holding_bucket_workorder_count_missing', 'runtime_approval_summary_holding_bucket_workorders_missing']`

## Exit Bucket Handoff
- status: `fail`
- attribution_present: `True`
- source_present: `True`
- runtime_candidate_count: `0`
- bucket_count ev/runtime/expected: `48` / `-1` / `48`
- workorder_count ev/runtime/expected: `10` / `-1` / `10`
- missing: `['runtime_approval_summary_exit_bucket_count_missing', 'runtime_approval_summary_exit_bucket_workorder_count_missing', 'runtime_approval_summary_exit_bucket_workorders_missing']`

## Lifecycle Flow Bucket Handoff
- status: `pass`
- attribution_present: `True`
- flow_count: `5583`
- complete_flow_count: `30`
- direct_sim_record_complete_flow_count: `0`
- adm_bridge_complete_flow_count: `30`
- fallback_complete_flow_count: `0`
- incomplete_flow_count: `5553`
- complete_flow_rate: `0.0054`
- join_contract_blocked: `False`
- bundle_ev_tuning_state: `ready_for_bundle_ev_tuning`
- top_incomplete_reason: `missing_submit`
- missing: `[]`

## AI Correction
- status: `missing`
- ai_status: `missing`
- provider_status: `-`
- blocking_runtime_candidate_families: `[]`
- parse_warnings: `[]`
- interpretation: `AI correction artifact missing or unreadable`

## Scalp Sim Overnight
- status: `pass`
- decision_target: `4`
- active_undecided_count: `0`
- decision_coverage_rate: `1.0`
- source_quality_status: `pass`
- source_quality_warnings: `[]`
- interpretation: `scalp sim overnight preclose decisions covered active sim positions`

## Entry Bucket Handoff
- status: `fail`
- expected_candidate_ids: `['entry_bucket_10', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_17', 'entry_bucket_5', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_8', 'entry_bucket_9']`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `['entry_bucket_10', 'entry_bucket_12', 'entry_bucket_13', 'entry_bucket_14', 'entry_bucket_17', 'entry_bucket_5', 'entry_bucket_6', 'entry_bucket_7', 'entry_bucket_8', 'entry_bucket_9']`
- missing_workorder_order_ids: `[]`
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
- policy_contract_missing: `['scale_in_policy_runtime_gap_ledger_missing']`
- policy_contract_interpretation: `Scale-in policy contract is not closed with source link, exclusion reason, and reopen trigger.`

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
- status: `fail`
- source_contract_status: `warning`
- ai_two_pass_review_status: `parsed`
- expected_candidate_ids: `['entry:chosen_action:no_buy_ai', 'entry:chosen_action:wait_requote', 'entry:exit_rule:exit_unknown', 'entry:exit_rule:scalp_soft_stop_pct', 'entry:liquidity_bucket:liquidity_high', 'entry:overbought_bucket:overbought_normal', 'entry:overbought_bucket:overbought_watch', 'entry:score_band:score_66_69', 'entry:score_band:score_70p', 'entry:source_stage:scalp_entry_action_decision_snapshot', 'entry:source_stage:wait6579_ev_cohort', 'entry:stale_bucket:fresh_or_unflagged', 'entry:strength_bucket:strong_strength_momentum', 'entry:strength_bucket:weak_strength_momentum', 'entry:time_bucket:time_1200_1400', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_stale_high_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
- live_auto_apply_families: `[]`
- missing_bridge_families: `[]`
- missing_runtime_summary_candidate_ids: `['entry:chosen_action:no_buy_ai', 'entry:chosen_action:wait_requote', 'entry:exit_rule:exit_unknown', 'entry:exit_rule:scalp_soft_stop_pct', 'entry:liquidity_bucket:liquidity_high', 'entry:overbought_bucket:overbought_normal', 'entry:overbought_bucket:overbought_watch', 'entry:score_band:score_66_69', 'entry:score_band:score_70p', 'entry:source_stage:scalp_entry_action_decision_snapshot', 'entry:source_stage:wait6579_ev_cohort', 'entry:stale_bucket:fresh_or_unflagged', 'entry:strength_bucket:strong_strength_momentum', 'entry:strength_bucket:weak_strength_momentum', 'entry:time_bucket:time_1200_1400', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_blocked_ai_score_stale_stale_block_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_bottoming_entry_allowed_st', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_stale_high_liquidity_li', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_blocked_ai_score_stale_fresh_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagge', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_confirmed_stale_stale_high_liquidity_liqu', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_f', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_entry_action_decision_snapshot_stale_s', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scalp_sim_panic_level1_entry_observed_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait6579_ev_cohort_stale_fresh_or_unflagged_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_stale_high_liquidity_liq', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_block_liquidit', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blocked_ai_score_stale_stale_not_available_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_scalp_sim_panic_level1_entry_observed_stale', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_combo_holding_flow_source_scalp_sim_ov', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex', 'lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex']`
- workorder_needed_bucket_ids: `[]`
- ai_post_apply_followup_bucket_ids: `[]`
- warnings: `['lifecycle_bucket_discovery_source_contract_warning', 'source_contract_drift_warning']`
- interpretation: `lifecycle bucket discovery produced surfaced candidates that downstream consumers dropped`

## LDM Hypothesis Parent Refinement
- status: `pass`
- input/consumed: `4` / `4`
- derived input/consumed: `0` / `0`
- derived_contract_drift_recompute_consumed: `False`
- closure_counts: `{'new_parent_candidate_created': 1, 'parent_refinement_candidate_created': 2, 'rare_observation_only_budget_capped': 1}`
- missing: `[]`
- warnings: `[]`
- contract_drift: `{'candidate_feature_event_count': 1956, 'recomputable_match_count': 1956, 'recomputable_hypothesis_ids': ['ldm_hypothesis_00d0b765311ad7aa', 'ldm_hypothesis_711caa66c89b3f51', 'ldm_hypothesis_92dfecb5a05caa64', 'ldm_hypothesis_e04e4d815fd8d0f9'], 'runtime_matched_event_count': 1956}`
- diagnosis_missing_warning_input_ids: `[]`
- diagnosis_missing_fail_input_ids: `[]`
- diagnosed_repeated_input_ids: `['ldm_refinement_7c5842bd79497668', 'ldm_refinement_eced95099ff6e892', 'ldm_refinement_5ddc816b3f7061d2', 'ldm_refinement_c5b11d2d65ace5ff']`
- runtime_authority_violation_input_ids: `[]`

## Active Sim Priority Handoff
- status: `fail`
- active_seed_ids: `['active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83']`
- observed_seed_ids: `['active_seed_03c539e6527cdda2', 'active_seed_7cf1c198fc1e5246', 'active_seed_b99a2dea7aac2a83']`
- missing: `['active_sim_priority_inactive_key_consumed']`
- warnings: `['active_sim_priority_preopen_handoff_pending']`
- match_absence_diagnosis: `inactive_or_unknown_key_consumed`
- match_absence_reason: `active_sim_priority_inactive_key_consumed`
- candidate_prefix_count: `1956`
- top_candidate_prefixes: `[('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_wait6579"}', 1011), ('{"entry_score_parent": "score_watch_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 624), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_wait6579"}', 252), ('{"entry_score_parent": "score_mid_recovery", "entry_source_parent": "entry_source_blocked_ai_score"}', 69)]`

## Lifecycle Bucket Windows
- status: `pass`
- checked: `True`
- windows: `{'rolling5d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 31, 'window_role': 'rolling_confirmation'}, 'rolling10d': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 44, 'window_role': 'rolling_confirmation'}, 'mtd': {'available': True, 'source_contract_status': 'pass', 'parent_granularity_status': 'target_pass', 'parent_bucket_count': 39, 'window_role': 'promotion_confirmation'}}`
- missing: `[]`
- warnings: `[]`

## Swing Lifecycle Handoff
- status: `missing`
- expected_candidate_ids: `[]`
- missing_ev_candidate_ids: `[]`
- missing_runtime_summary_candidate_ids: `[]`
- missing_workorder_order_ids: `[]`
- daily_simulation_consumed: `False`
- ai_two_pass_review_status: `-`
- warnings: `[]`
- interpretation: `Swing LDM report missing`

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
- generation_id: `2026-06-25-0cfd8429982c`
- source_hash: `0cfd8429982c49d5de9b46e51f11628781313d3348cf3c907ddb0fb852872896`
- snapshot_status: `first_generation`
- previous_generation_id: `-`
- previous_source_hash: `-`
- new_order_ids: `['order_entry_broker_receipt_contract_gap_review', 'order_entry_fill_quality_contract_gap_review', 'order_entry_post_submit_contract_gap_review', 'order_entry_source_taxonomy_contract_gap_review', 'order_entry_submit_drought_auto_resolution', 'order_entry_telegram_post_submit_contract_gap_review', 'order_lifecycle_entry_bucket_chosen_action_no_buy_ai', 'order_lifecycle_entry_bucket_chosen_action_wait_requote', 'order_lifecycle_entry_bucket_exit_rule_exit_unknown', 'order_lifecycle_entry_bucket_exit_rule_scalp_soft_stop_pct', 'order_lifecycle_entry_bucket_liquidity_bucket_liquidity_high', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_normal', 'order_lifecycle_entry_bucket_overbought_bucket_overbought_watch', 'order_lifecycle_entry_bucket_score_band_score_60_62', 'order_lifecycle_entry_bucket_score_band_score_66_69', 'order_lifecycle_entry_bucket_score_band_score_70p', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913', 'order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_daily_limit_up_immediate_exit_outc_960ea129', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_good_e_d8c33947', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_missed_30bb5c8f', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_hard_stop_pct_outcome_neutra_d5168c3c', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_good_e_71b132b9', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_missed_bb293be8', 'order_lifecycle_exit_bucket_combo_exit_result_source_sim_post_sell_evaluation_rule_scalp_soft_stop_pct_outcome_neutra_d73738ba', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_25002a6e', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_e48e520c', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_5e11e397', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_c0394ca1', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_b5237a42', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_cd847d1b', 'order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_fabcf0d3', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_holding_action_not_applicable_a_fc555278', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_lt_neg070_he_ed505a3f', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_neg070_neg01_7ffc2d26', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos080_pos15_aaaecaaf', 'order_lifecycle_holding_bucket_combo_holding_flow_source_scalp_sim_holding_started_action_wait_profit_profit_pos150_pos30_6f3188b0', 'order_lifecycle_holding_bucket_held_bucket_held_not_applicable_at_start_508784a3', 'order_lifecycle_holding_bucket_holding_action_holding_action_not_applicable_at_start_c20ec935', 'order_lifecycle_holding_bucket_holding_action_wait_c26d74df', 'order_lifecycle_holding_bucket_holding_source_stage_scalp_sim_holding_started_78913f30', 'order_lifecycle_holding_bucket_profit_band_profit_lt_neg070_711f1b3f', 'order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_parent_conflict_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`
