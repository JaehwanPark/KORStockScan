# Lifecycle Decision Matrix - 2026-08-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-13`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2860`
- source_rows_total: `3718`
- retained_rows: `2860`
- dropped_rows_by_source: `{'dedupe': 858}`
- joined_rows: `1146`
- policy_pass_count: `4`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `21` / `8`
- exit_bucket_count/workorders: `28` / `5`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `32`
- lifecycle_flow_complete_count: `7`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `7` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0029`
- incomplete_flow_reason_counts: `{'missing_submit': 2348, 'missing_holding': 2382, 'missing_exit': 1246, 'missing_entry': 2256, 'sim_record_id_only': 4, 'scale_in_noise_only': 1113, 'candidate_id_only': 2251, 'postclose_exit_without_entry': 1142}`
- bucket_directed_sim_probe: `{'observed_row_count': 1210, 'matched_row_count': 0, 'background_row_count': 1210, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 50, 'not_instrumented': 1160}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 511 | 5 | 0.1585 | 0.0049 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 59 | 14 | -0.2695 | 0.3322 | `pass` | `NO_CHANGE` | False |
| `holding` | 24 | 14 | -0.4707 | 0.8167 | `pass` | `EXIT` | False |
| `scale_in` | 1113 | 1099 | -0.6633 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1153 | 14 | -0.4537 | 0.017 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2395, 'complete_flow_count': 7, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 7, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 4, 'direct_sim_record_incomplete_flow_count': 4, 'direct_sim_record_stage_coverage_counts': {'holding': 3, 'exit': 3}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 4, 'missing_submit': 4, 'missing_holding': 1, 'missing_exit': 1, 'sim_record_id_only': 4, 'scale_in_noise_only': 1, 'postclose_exit_without_entry': 3}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 2388, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2860, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0029, 'complete_flow_conversion_denominator': 1150, 'complete_flow_conversion_rate': 0.0061, 'active_priority_incomplete_seed_count': 132, 'scale_in_followup_event_count': 1113, 'scale_in_unique_flow_count': 802, 'scale_in_noise_flow_count': 1113, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1113, 'active_priority_incomplete_seed_excluded': 132}, 'conversion_blocker_reason_counts': {'missing_entry': 1143, 'missing_holding': 1140, 'missing_exit': 1, 'missing_submit': 1142, 'sim_record_id_only': 3, 'postclose_exit_without_entry': 1142, 'candidate_id_only': 1139}, 'observation_seed_reason_counts': {'missing_submit': 1206, 'missing_holding': 1242, 'missing_exit': 1245, 'missing_entry': 1113, 'sim_record_id_only': 1, 'scale_in_noise_only': 1113, 'candidate_id_only': 1112}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 511, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 511}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 59, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 59}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 24, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 21, 'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1113, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1, 'candidate_id': 1112}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1153, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 11, 'exact_sim_record_id': 3, 'candidate_id': 1139}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 511, 'submit': 59, 'holding': 24, 'exit': 1153}, 'incomplete_flow_reason_counts': {'missing_submit': 2348, 'missing_holding': 2382, 'missing_exit': 1246, 'missing_entry': 2256, 'sim_record_id_only': 4, 'scale_in_noise_only': 1113, 'candidate_id_only': 2251, 'postclose_exit_without_entry': 1142}, 'bucket_count': 32, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:f2f4676367` | 1 | 1 | 0.1639 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f15e79e2f2` | 1 | 1 | -1.3447 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d3cb9791fb` | 1 | 1 | -1.7547 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d95dd39f2f` | 1 | 1 | 0.2263 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:88970cb1c3` | 1 | 1 | 0.5237 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:98d7e78cc5` | 1 | 1 | -0.8911 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:24baa9225d` | 1 | 1 | -0.4777 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 965 | 951 | -0.8045 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 148 | 148 | 0.2435 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:833cd81ca4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:9844731079` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:46d664a3b5` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:d5c09f3b03` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 5 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:9eb64b35a4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 15 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:40a7fd3277` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:615d24b8d0` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 511, 'bucket_count': 135, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 308 | 5 | 0.1585 | -1.67 | 0.4 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 43 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 21 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 138 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 5 | 2 | 0.5387 | -1.56 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 1 | 0.4159 | 0.12 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 1 | -1.1812 | -1.46 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1200_1400` | 6 | 1 | 0.4803 | -3.89 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 59, 'bucket_count': 86, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 67, 'refresh_applied_count': 30, 'still_latency_blocked_after_refresh_count': 42, 'latency_pass_recovered_count': 8, 'order_bundle_submitted_after_refresh_count': 0, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 5, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 90, 'ws_snapshot_refresh_failed_stale': 11}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 5, 'ws_snapshot_refresh_failed_input_snapshot_fresh': 90, 'ws_snapshot_refresh_failed_stale': 11}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 2, 'entry_ai_authority_revalidation': 6}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_attempted_unresolved': 21, 'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 7, 'refresh_resolved_quote_freshness': 8, 'sim_submit_path_not_applicable': 22}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 22, 'refresh_not_attempted_or_not_instrumented': 7, 'sim_submit_path_not_applicable': 22, 'ws_snapshot_refresh_applied': 8}, 'real_submitted_row_count': 5, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 54 | 14 | -0.2695 | `keep_collecting` |
| `actual_order_submitted` | `true` | 5 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 54 | 14 | -0.2695 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 5 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_attempted_unresolved|fill=false|submitted=false` | 21 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 8 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 4 | -0.1938 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.2779 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 1 | 0.9116 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.8951 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 1 | 0.1659 | `source_quality_workorder` |
| `combo_submit_quality` | `source=entry_submit_revalidation_block|revalidation=warning_observed_mark_gap_unresolved|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=latency_unknown|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 22 | 14 | -0.2695 | `keep_collecting` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 6 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_state` | `danger` | 30 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 22 | 14 | -0.2695 | `keep_collecting` |
| `latency_state` | `caution` | 5 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 36 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 13 | 6 | 0.0504 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 10 | 8 | -0.5094 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 37 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 13 | 6 | 0.0504 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 9 | 8 | -0.5094 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 37 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 17 | 10 | -0.1253 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 5 | 4 | -0.6299 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 37 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 22 | 14 | -0.2695 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 28 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 22 | 14 | -0.2695 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 24, 'source_row_count': 24, 'bucket_count': 21, 'joined_sample': 70, 'source_quality_adjusted_ev_pct': -0.4707, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 8, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.4603 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -0.8125 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.2827 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.1159 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.5237 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 21 | 14 | -0.4707 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 15 | 9 | -0.5012 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 5 | -0.4158 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 21 | 14 | -0.4707 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.216 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -1.0481 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 7 | 4 | -0.4603 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.5237 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `profit_band` / `profit_neg070_neg010` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1153, 'source_row_count': 1153, 'bucket_count': 28, 'joined_sample': 70, 'source_quality_adjusted_ev_pct': -0.4537, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | -0.2925 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.2375 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.1639 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.7547 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | 0.0899 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.5237 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1139 | 0 | None | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -0.5849 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 4 | 4 | -0.3651 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.2375 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.6274 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1139 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -0.2068 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.2375 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.5904 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -1.5057 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1139 | 0 | None | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 11 | 11 | -0.5127 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.2375 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1139 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.216 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -1.0481 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.4009 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.5237 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1139 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `exit_outcome` / `NEUTRAL` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `MISSED_UPSIDE` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_source_stage` / `sim_post_sell_evaluation` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `profit_band` / `profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1113, 'bucket_count': 142, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 148, 'AVG_DOWN': 965}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1096 | 1096 | None | -0.743 | 0.1195 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2 | 2 | None | 0.93 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 15 | 1 | None | 0.25 | 1.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 507 | 507 | None | -0.6614 | 0.1598 | `hold_sample` |
| `ai_score_source` | `live` | 434 | 434 | None | -0.8758 | 0.0968 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 73 | 73 | None | -0.5896 | 0.0137 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 53 | 53 | None | -0.7038 | 0.0566 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 31 | 31 | None | -0.54 | 0.1935 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | 0.25 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 14 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 965 | 951 | None | -0.8891 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 148 | 148 | None | 0.2247 | 0.9054 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 963 | 949 | None | -0.8831 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 148 | 148 | None | 0.2247 | 0.9054 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2 | 2 | None | -3.73 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 142 | 142 | None | 0.2274 | 0.9014 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 53 | 53 | None | -0.87 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.50)` | 43 | 43 | None | -0.5 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 35 | 35 | None | -0.76 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 32 | 32 | None | -1.0 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'observation_state': 'observed', 'observation_reason': 'overnight_pipeline_rows_available', 'source_artifact_present': True, 'overnight_rows': 6, 'bucket_count': 16, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 3, 'SELL_TODAY': 3}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 3 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `stage` | `holding` | 3 | 0 | None | None | None | `hold_sample` |

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
