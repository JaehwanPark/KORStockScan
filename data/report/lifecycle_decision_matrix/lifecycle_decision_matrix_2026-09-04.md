# Lifecycle Decision Matrix - 2026-09-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-04`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1087`
- source_rows_total: `1547`
- retained_rows: `1087`
- dropped_rows_by_source: `{'dedupe': 460}`
- joined_rows: `536`
- policy_pass_count: `2`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `1`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `14` / `0`
- exit_bucket_count/workorders: `21` / `8`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `30`
- lifecycle_flow_complete_count: `5`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `5` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0078`
- incomplete_flow_reason_counts: `{'missing_holding': 636, 'missing_exit': 635, 'missing_submit': 592, 'missing_entry': 514, 'postclose_exit_without_entry': 2, 'candidate_id_only': 523, 'scale_in_noise_only': 512, 'sim_record_id_only': 5}`
- bucket_directed_sim_probe: `{'observed_row_count': 35, 'matched_row_count': 0, 'background_row_count': 35, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 9, 'policy_disabled': 26}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 506 | 10 | 3.0693 | 0.0198 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 51 | 2 | 0.2001 | 0.0078 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 7 | 2 | -0.7021 | 0.0571 | `hold_sample` | `EXIT` | False |
| `scale_in` | 512 | 512 | -0.6667 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 11 | 10 | -0.6752 | 0.9091 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 642, 'complete_flow_count': 5, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 5, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 5, 'direct_sim_record_incomplete_flow_count': 5, 'direct_sim_record_stage_coverage_counts': {}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 5, 'missing_submit': 5, 'missing_holding': 5, 'missing_exit': 5, 'sim_record_id_only': 5, 'scale_in_noise_only': 5}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 637, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1087, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0078, 'complete_flow_conversion_denominator': 7, 'complete_flow_conversion_rate': 0.7143, 'active_priority_incomplete_seed_count': 123, 'scale_in_followup_event_count': 512, 'scale_in_unique_flow_count': 406, 'scale_in_noise_flow_count': 512, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 512, 'active_priority_incomplete_seed_excluded': 123}, 'conversion_blocker_reason_counts': {'missing_entry': 2, 'missing_submit': 2, 'postclose_exit_without_entry': 2, 'missing_holding': 1, 'candidate_id_only': 1}, 'observation_seed_reason_counts': {'missing_holding': 635, 'missing_exit': 635, 'missing_submit': 590, 'candidate_id_only': 522, 'missing_entry': 512, 'scale_in_noise_only': 512, 'sim_record_id_only': 5}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 506, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 491, 'candidate_id': 15}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 51, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 51}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 7, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 7}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 512, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 507, 'exact_sim_record_id': 5}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 11, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 10, 'candidate_id': 1}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 506, 'submit': 51, 'holding': 7, 'exit': 11}, 'incomplete_flow_reason_counts': {'missing_holding': 636, 'missing_exit': 635, 'missing_submit': 592, 'missing_entry': 514, 'postclose_exit_without_entry': 2, 'candidate_id_only': 523, 'scale_in_noise_only': 512, 'sim_record_id_only': 5}, 'bucket_count': 30, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -0.75 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8880885eab` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:75fd5e9cb6` | 1 | 1 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f907ee6429` | 1 | 1 | -0.89 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 512 | 512 | -0.6667 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 7 | 7 | 3.9599 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 1 | 1 | 2.5732 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:18c5a6106d` | 4 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 12 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:187c221909` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f0786a34b` | 15 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:aee02bd6b3` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:415cf47417` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c08b979e6d` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 506, 'bucket_count': 142, 'actionable_bucket_count': 1, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 1}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 167 | 8 | 3.7866 | 6.2428 | 0.75 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 283 | 2 | 0.2001 | -1.59 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 37 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 2 | 2 | 1.7102 | 5.204 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 0.4531 | -1.7 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 1 | -0.053 | -1.48 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 1 | 2.5732 | 2.8229 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1200_1400` | 1 | 1 | 7.2965 | 12.0784 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 1 | 1 | 0.8222 | 0.0397 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | 7.8997 | 12.189 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 1 | 1 | 0.1426 | 0.0 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1400_close` | 1 | 1 | 8.1383 | 12.4042 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=blocked_ai_score|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 262 | 10 | 3.0693 | 4.6762 | 0.6 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 51, 'bucket_count': 79, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 13, 'refresh_applied_count': 13, 'still_latency_blocked_after_refresh_count': 10, 'latency_pass_recovered_count': 2, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 11, 'ws_snapshot_refresh_failed_stale': 1}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_input_snapshot_fresh': 11, 'ws_snapshot_refresh_failed_stale': 1}, 'latency_pass_recovered_downstream_counts': {'entry_ai_authority_revalidation': 2}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 1, 'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 9, 'refresh_resolved_quote_freshness': 34, 'sim_submit_path_not_applicable': 6}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 2, 'refresh_not_attempted_or_not_instrumented': 9, 'sim_submit_path_not_applicable': 6, 'ws_snapshot_refresh_applied': 34}, 'real_submitted_row_count': 3, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 48 | 2 | 0.2001 | `keep_collecting` |
| `actual_order_submitted` | `true` | 3 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 48 | 2 | 0.2001 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 3 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 34 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 1 | -0.053 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 1 | 0.4531 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 27 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 6 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 6 | 2 | 0.2001 | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 36 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 6 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 6 | 2 | 0.2001 | `keep_collecting` |
| `latency_state` | `safe` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 1 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 45 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 6 | 2 | 0.2001 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 45 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 6 | 2 | 0.2001 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 45 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 5 | 2 | 0.2001 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 45 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 5 | 2 | 0.2001 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 35 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 10 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 6 | 2 | 0.2001 | `keep_collecting` |
| `pre_submit_refresh_applied` | `ws_snapshot_refresh_applied` | 34 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 7, 'source_row_count': 7, 'bucket_count': 14, 'joined_sample': 10, 'source_quality_adjusted_ev_pct': -0.7021, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -0.7021 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 6 | 2 | -0.7021 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 5 | 2 | -0.7021 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 6 | 2 | -0.7021 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -0.7021 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 11, 'source_row_count': 11, 'bucket_count': 21, 'joined_sample': 50, 'source_quality_adjusted_ev_pct': -0.6752, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 8, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 5 | 5 | -0.882 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7021 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 1 | 1 | -0.65 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 6 | 6 | -0.8433 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -0.5064 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 6 | 6 | -0.8433 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.7021 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1437 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 6 | 6 | -0.8433 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3 | 3 | -0.5064 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -0.8306 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 3 | 3 | -0.3125 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_not_applicable_context_noop` | 1 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `profit_band` / `profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 512, 'bucket_count': 54, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 512}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 512 | 512 | None | -0.71 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 366 | 366 | None | -0.6923 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 72 | 72 | None | -0.8625 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 33 | 33 | None | -0.7573 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 32 | 32 | None | -0.5537 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 5 | 5 | None | -0.816 | 0.0 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 4 | 4 | None | -0.31 | 0.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 512 | 512 | None | -0.71 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 512 | 512 | None | -0.71 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.56)` | 97 | 97 | None | -0.56 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 78 | 78 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 65 | 65 | None | -0.72 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 42 | 42 | None | -0.86 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 39 | 39 | None | -0.75 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 34 | 34 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.65)` | 29 | 29 | None | -0.65 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 23 | 23 | None | -0.89 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 12 | 12 | None | -1.05 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 11 | 11 | None | -1.06 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 10 | 10 | None | -0.54 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `holding` | 1 | 0 | None | None | None | `hold_sample` |

### Overnight Bucket Runtime Approval Candidates

- none

### Overnight Bucket Workorders

- none

## Fixed Threshold Roles

- `hard_safety`: broker_submit_guard, stale_quote_submit_block, price_freshness_guard, hard_stop, protect_stop, emergency_stop, account_order_cooldown_qty_guard
- `baseline_prior`: BUY_SCORE_THRESHOLD, VPW_MIN_SCORE, strength_momentum_cutoff, entry_score_cutoff
- `bounded_tunable`: SCALP_ENTRY_LATENCY_MAX_WS_AGE_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION, SCALP_ENTRY_LATENCY_MAX_SPREAD_RATIO_FOR_CAUTION, score65_74_recovery_probe, soft_stop_whipsaw_confirmation, holding_flow_override, scale_in_price_guard
- `legacy_archive`: fallback_scout_main, fallback_single, latency_fallback_split_entry, legacy_latency_composite, closed_shadow_axes

## Forbidden Uses

- `hard_safety_override`
- `real_execution_quality_from_sim_only`
- `intraday_threshold_mutation`
- `runtime_feature_future_label_leakage`
