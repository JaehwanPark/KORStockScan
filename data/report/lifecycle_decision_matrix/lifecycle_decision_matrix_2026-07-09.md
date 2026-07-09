# Lifecycle Decision Matrix - 2026-07-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-09`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1243`
- source_rows_total: `1761`
- retained_rows: `1243`
- dropped_rows_by_source: `{'dedupe': 518}`
- joined_rows: `541`
- policy_pass_count: `4`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `17` / `5`
- exit_bucket_count/workorders: `38` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `49`
- lifecycle_flow_complete_count: `10`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `10` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0092`
- incomplete_flow_reason_counts: `{'missing_submit': 1054, 'missing_holding': 1071, 'missing_exit': 537, 'missing_entry': 1023, 'sim_record_id_only': 16, 'scale_in_noise_only': 478, 'candidate_id_only': 1018, 'postclose_exit_without_entry': 545}`
- bucket_directed_sim_probe: `{'observed_row_count': 620, 'matched_row_count': 0, 'background_row_count': 620, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 75, 'not_instrumented': 545}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 125 | 4 | -0.2565 | 0.0128 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 45 | 13 | -0.4773 | 0.3756 | `pass` | `NO_CHANGE` | False |
| `holding` | 24 | 13 | -1.1943 | 0.7042 | `pass` | `EXIT` | False |
| `scale_in` | 491 | 485 | -1.1616 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 558 | 26 | -1.0692 | 0.1211 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1092, 'complete_flow_count': 10, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 10, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 16, 'direct_sim_record_incomplete_flow_count': 16, 'direct_sim_record_stage_coverage_counts': {'holding': 2, 'exit': 13}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 16, 'missing_submit': 16, 'missing_holding': 14, 'missing_exit': 3, 'sim_record_id_only': 16, 'scale_in_noise_only': 3, 'postclose_exit_without_entry': 13}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 1082, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 1243, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0092, 'complete_flow_conversion_denominator': 555, 'complete_flow_conversion_rate': 0.018, 'active_priority_incomplete_seed_count': 59, 'scale_in_followup_event_count': 491, 'scale_in_unique_flow_count': 445, 'scale_in_noise_flow_count': 478, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 478, 'active_priority_incomplete_seed_excluded': 59}, 'conversion_blocker_reason_counts': {'missing_entry': 545, 'missing_submit': 545, 'sim_record_id_only': 13, 'postclose_exit_without_entry': 545, 'missing_holding': 543, 'candidate_id_only': 532}, 'observation_seed_reason_counts': {'missing_submit': 509, 'missing_holding': 528, 'missing_exit': 537, 'missing_entry': 478, 'sim_record_id_only': 3, 'scale_in_noise_only': 478, 'candidate_id_only': 486}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 125, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 114, 'candidate_id': 11}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 45, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 45}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 24, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 22, 'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 491, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 16, 'candidate_id': 475}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 558, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 11, 'exact_sim_record_id': 15, 'candidate_id': 532}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 125, 'submit': 45, 'holding': 24, 'exit': 558}, 'incomplete_flow_reason_counts': {'missing_submit': 1054, 'missing_holding': 1071, 'missing_exit': 537, 'missing_entry': 1023, 'sim_record_id_only': 16, 'scale_in_noise_only': 478, 'candidate_id_only': 1018, 'postclose_exit_without_entry': 545}, 'bucket_count': 49, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.9899 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9b3d586d84` | 1 | 1 | -1.2667 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3ecc9eeb81` | 1 | 1 | 0.9467 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.3812 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5e39da79b4` | 1 | 1 | -4.7933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b19e5449ca` | 1 | 1 | 0.2149 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:6b32e9a089` | 1 | 1 | -2.3218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:daa27da05b` | 1 | 1 | 1.9895 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:86c7f4aa07` | 1 | 1 | 1.3047 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 438 | 433 | -1.358 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 40 | 39 | 0.9778 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 9 | 9 | -1.1178 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 2 | 2 | -1.265 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 2 | 2 | -0.205 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8cfdf34d0a` | 1 | 1 | -1.38 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:84a094a614` | 1 | 1 | -1.53 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:12b48c8f43` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:fef5ae20be` | 3 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:04fe106012` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 125, 'bucket_count': 96, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 58 | 3 | 0.7496 | 0.32 | 0.6667 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 10 | 1 | -3.2749 | -6.17 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 11 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 44 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 1 | 1.0876 | -3.85 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 1 | -1.1947 | 3.18 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 4 | 1 | -3.2749 | -6.17 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 1 | 2.356 | 1.63 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 45, 'bucket_count': 81, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 18, 'refresh_applied_count': 17, 'still_latency_blocked_after_refresh_count': 1, 'latency_pass_recovered_count': 8, 'order_bundle_submitted_after_refresh_count': 5, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_stale': 1}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_stale': 1}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 5, 'price_guard_or_revalidation': 3}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 1, 'refresh_not_attempted_or_not_instrumented': 12, 'refresh_resolved_quote_freshness': 10, 'sim_submit_path_not_applicable': 22}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 1, 'refresh_not_attempted_or_not_instrumented': 12, 'sim_submit_path_not_applicable': 22, 'ws_snapshot_refresh_applied': 10}, 'real_submitted_row_count': 12, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 33 | 13 | -0.4773 | `keep_collecting` |
| `actual_order_submitted` | `true` | 12 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 33 | 13 | -0.4773 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 12 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 8 | 3 | 0.7496 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | -1.0203 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | 0.1828 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -2.0311 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.8585 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 22 | 13 | -0.4773 | `keep_collecting` |
| `latency_reason` | `other_danger` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 7 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 22 | 13 | -0.4773 | `keep_collecting` |
| `latency_state` | `danger` | 11 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 7 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 5 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 23 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 13 | 5 | -0.3626 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 9 | 8 | -0.5489 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 23 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 13 | 5 | -0.3626 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 9 | 8 | -0.5489 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 23 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 19 | 10 | -0.1284 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 2 | 2 | -2.0311 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.8585 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 23 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 21 | 12 | -0.4455 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 1 | 1 | -0.8585 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 24, 'source_row_count': 24, 'bucket_count': 17, 'joined_sample': 65, 'source_quality_adjusted_ev_pct': -1.1943, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -2.2202 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.6471 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 0.2149 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.9467 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 22 | 13 | -1.1943 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 22 | 13 | -1.1943 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 22 | 13 | -1.1943 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 11 | 9 | -2.2202 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.2149 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.9467 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 558, 'source_row_count': 558, 'bucket_count': 38, 'joined_sample': 130, 'source_quality_adjusted_ev_pct': -1.0692, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 1, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.4125 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 4 | 4 | -0.5225 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.6894 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -1.0913 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -2.4442 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.39 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -4.7933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.3218 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 0.9467 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.2149 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 520 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 13 | 13 | -1.0 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.2598 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 3 | 3 | -1.3139 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 2 | 2 | -3.5575 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 2 | 2 | -1.0913 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 532 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 13 | 13 | -1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -2.0464 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 1.1139 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0913 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 1 | 1 | -4.7933 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 12 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 520 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 13 | 13 | -1.0 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 11 | 11 | -1.1469 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0913 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 12 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 520 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 17 | 17 | -1.7973 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.5225 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.39 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 0.2149 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.9467 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 532 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `exit_outcome` / `outcome_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_rule` / `scalp_soft_stop_pct` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_rule` / `scalp_trailing_take_profit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 491, 'bucket_count': 214, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 42, 'AVG_DOWN': 449}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 421 | 420 | None | -1.4296 | 0.0619 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 35 | 35 | None | -0.7363 | 0.2571 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 15 | 15 | None | -1.3653 | 0.0667 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 11 | 11 | None | -1.3336 | 0.1818 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3 | 3 | None | -1.98 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 6 | 1 | None | 2.08 | 1.0 | `hold_sample` |
| `ai_score_source` | `live` | 360 | 360 | None | -1.4636 | 0.0694 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 63 | 63 | None | -1.4805 | 0.0317 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 53 | 52 | None | -0.8933 | 0.1346 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 7 | 7 | None | -0.2771 | 0.2857 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 2 | 2 | None | 0.625 | 1.0 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 1 | 1 | None | 2.08 | 1.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 5 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 449 | 444 | None | -1.5836 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 42 | 41 | None | 0.9249 | 0.9512 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 439 | 434 | None | -1.5453 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 42 | 41 | None | 0.9249 | 0.9512 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 10 | 10 | None | -3.248 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 17 | 17 | None | 0.4306 | 0.9412 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 15 | 15 | None | -0.9053 | 0.1333 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 4, 'bucket_count': 18, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 2, 'SELL_TODAY': 2}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.035 | -1.38 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -1.035 | -1.38 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_lt040` | 2 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `stage` | `holding` | 2 | 0 | None | None | None | `hold_sample` |

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
