# Lifecycle Decision Matrix - 2026-07-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-08`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3609`
- source_rows_total: `4979`
- retained_rows: `3609`
- dropped_rows_by_source: `{'dedupe': 1370}`
- joined_rows: `1470`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `26` / `7`
- exit_bucket_count/workorders: `40` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `76`
- lifecycle_flow_complete_count: `20`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `20` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0063`
- incomplete_flow_reason_counts: `{'missing_exit': 1488, 'missing_submit': 3136, 'missing_holding': 3149, 'missing_entry': 3047, 'postclose_exit_without_entry': 1688, 'candidate_id_only': 3040, 'sim_record_id_only': 38, 'scale_in_noise_only': 1352}`
- bucket_directed_sim_probe: `{'observed_row_count': 1914, 'matched_row_count': 0, 'background_row_count': 1914, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'not_instrumented': 1695, 'policy_missing': 219}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 340 | 19 | -0.2534 | 0.1062 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 101 | 30 | -0.4432 | 0.8911 | `pass` | `NO_CHANGE` | False |
| `holding` | 78 | 30 | -1.4513 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 1373 | 1338 | -0.9143 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1717 | 53 | -1.221 | 0.1636 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 3196, 'complete_flow_count': 20, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 20, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 38, 'direct_sim_record_incomplete_flow_count': 38, 'direct_sim_record_stage_coverage_counts': {'holding': 4, 'exit': 23}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 38, 'missing_submit': 38, 'missing_holding': 34, 'missing_exit': 15, 'sim_record_id_only': 38, 'scale_in_noise_only': 15, 'postclose_exit_without_entry': 23}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 3176, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 3609, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0063, 'complete_flow_conversion_denominator': 1715, 'complete_flow_conversion_rate': 0.0117, 'active_priority_incomplete_seed_count': 129, 'scale_in_followup_event_count': 1373, 'scale_in_unique_flow_count': 1259, 'scale_in_noise_flow_count': 1352, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1352, 'active_priority_incomplete_seed_excluded': 129}, 'conversion_blocker_reason_counts': {'missing_entry': 1695, 'missing_holding': 1689, 'missing_exit': 7, 'postclose_exit_without_entry': 1688, 'missing_submit': 1687, 'sim_record_id_only': 23, 'candidate_id_only': 1664}, 'observation_seed_reason_counts': {'missing_exit': 1481, 'missing_submit': 1449, 'missing_holding': 1460, 'candidate_id_only': 1376, 'missing_entry': 1352, 'sim_record_id_only': 15, 'scale_in_noise_only': 1352}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 340, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 301, 'candidate_id': 39}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 101, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 101}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 78, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 74, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1373, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 36, 'candidate_id': 1337}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1717, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 26, 'exact_sim_record_id': 27, 'candidate_id': 1664}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 340, 'submit': 101, 'holding': 78, 'exit': 1717}, 'incomplete_flow_reason_counts': {'missing_exit': 1488, 'missing_submit': 3136, 'missing_holding': 3149, 'missing_entry': 3047, 'postclose_exit_without_entry': 1688, 'candidate_id_only': 3040, 'sim_record_id_only': 38, 'scale_in_noise_only': 1352}, 'bucket_count': 76, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9cad8b8252` | 1 | 1 | -2.0092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.6035 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:d284f9c76b` | 1 | 1 | -0.7822 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9f155f5933` | 1 | 1 | -2.6744 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:fa72bf4c37` | 1 | 1 | -1.4651 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c664272a40` | 1 | 1 | 1.6352 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 1 | 1 | -1.0257 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ceba1530ad` | 1 | 1 | -2.2738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:446333cd75` | 1 | 1 | -3.0007 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:15086b5007` | 1 | 1 | -1.5174 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:80242605fa` | 1 | 1 | -2.2092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:9d93306fa4` | 1 | 1 | -1.2497 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6a4f3e4bd4` | 1 | 1 | -1.9122 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2f0e6b68fc` | 1 | 1 | -2.6232 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ffc82782b8` | 1 | 1 | -0.6063 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:71fbf5a01b` | 1 | 1 | -1.8392 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3218d874d9` | 1 | 1 | 3.3556 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:56bc096203` | 1 | 1 | -1.8389 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1143 | 1113 | -1.2047 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 340, 'bucket_count': 150, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 282 | 15 | -0.1279 | -2.2907 | 0.2 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 16 | 3 | -0.4373 | -0.5423 | 0.0 | `hold_sample` |
| `chosen_action` | `DROP` | 1 | 1 | -1.5834 | -2.3793 | 0.0 | `hold_sample` |
| `chosen_action` | `ALLOW_BOTTOMING_ENTRY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 34 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 11 | 3 | 0.1944 | -1.2467 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 3 | 2 | -1.2566 | -3.58 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 3 | 2 | -0.1036 | -3.605 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | -0.5861 | -0.7237 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 6 | 1 | -1.1183 | -3.37 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 17 | 1 | 0.9508 | -3.0 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 11 | 1 | 1.2081 | -3.35 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 15 | 1 | 0.5596 | -3.45 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_1200_1400` | 1 | 1 | -2.3188 | -4.68 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | -0.1396 | -0.1796 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | -1.5834 | -2.3793 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 1 | 1.2143 | -4.12 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 17 | 1 | -2.2858 | 1.03 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 3 | 1 | 2.0083 | 4.69 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 12 | 12 | -0.1721 | -3.58 | 0.0 | `hold_no_edge` |
| `liquidity_bucket` | `liquidity_high` | 255 | 19 | -0.2534 | -2.0193 | 0.1579 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 236 | 16 | -0.1825 | -2.2498 | 0.125 | `hold_no_edge` |
| `score_band` | `score_60_62` | 153 | 10 | -0.2649 | -2.875 | 0.1 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 210 | 15 | -0.1279 | -2.2907 | 0.2 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 226 | 12 | 0.1671 | -1.8875 | 0.1667 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 101, 'bucket_count': 77, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 15, 'refresh_applied_count': 14, 'still_latency_blocked_after_refresh_count': 4, 'latency_pass_recovered_count': 5, 'order_bundle_submitted_after_refresh_count': 1, 'refresh_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_missing': 2}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_invalid': 1, 'ws_snapshot_refresh_failed_stale': 2, 'ws_snapshot_refresh_failed_missing': 2}, 'latency_pass_recovered_downstream_counts': {'budget_pass_no_submit_event': 1, 'order_bundle_submitted': 1, 'price_guard_or_revalidation': 3}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 24, 'refresh_resolved_quote_freshness': 3, 'sim_submit_path_not_applicable': 74}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 24, 'sim_submit_path_not_applicable': 74, 'ws_snapshot_refresh_applied': 3}, 'real_submitted_row_count': 24, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 77 | 30 | -0.4432 | `keep_collecting` |
| `actual_order_submitted` | `true` | 24 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 77 | 30 | -0.4432 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 24 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 22 | 9 | 0.1056 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 8 | -0.3612 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 6 | -0.4192 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 4 | 0.2492 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.9788 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.2748 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -8.5432 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 74 | 30 | -0.4432 | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 13 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 11 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 2 | 0 | None | `keep_collecting` |
| `latency_reason` | `other_danger` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 74 | 30 | -0.4432 | `keep_collecting` |
| `latency_state` | `safe` | 13 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 11 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 3 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 42 | 17 | -0.1141 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 32 | 13 | -0.8737 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 27 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 42 | 17 | -0.1141 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 32 | 13 | -0.8737 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 27 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 67 | 27 | -0.1281 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 27 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 5 | 1 | 0.9788 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -5.409 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 72 | 28 | -0.0885 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 27 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 2 | 2 | -5.409 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 74 | 30 | -0.4432 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 78, 'source_row_count': 78, 'bucket_count': 26, 'joined_sample': 150, 'source_quality_adjusted_ev_pct': -1.4513, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 21 | 21 | -2.179 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.0733 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.6573 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3082 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 3.3556 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 42 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 74 | 30 | -1.4513 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 72 | 30 | -1.4513 | `candidate_tighten_or_exclude` |
| `holding_action` | `DROP` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 74 | 30 | -1.4513 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 21 | 21 | -2.179 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 3 | 0.0733 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | -0.6573 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 3 | 2 | 0.3082 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 3.3556 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 44 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_pos150_pos300` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1717, 'source_row_count': 1717, 'bucket_count': 40, 'joined_sample': 265, 'source_quality_adjusted_ev_pct': -1.221, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 17 | 17 | -1.2671 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 9 | 9 | -2.4419 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.3142 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 4 | 4 | -0.5875 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -2.1572 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 0.5145 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | -0.06 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.153 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | -3.0007 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -6.7982 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.6636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 3.3556 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 55 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 1609 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 23 | 23 | -0.9042 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 13 | 13 | -1.0454 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 10 | 10 | -2.4977 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1668 | 4 | 0.2812 | `source_quality_workorder` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -2.1572 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 23 | 23 | -0.9042 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 20 | 20 | -1.9481 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | 0.2812 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 0.9302 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 1 | 1 | -3.0007 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 1 | 1 | -6.7982 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 1664 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 26 | 26 | -1.7323 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 23 | 23 | -0.9042 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | 0.2812 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 55 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1609 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 38 | 38 | -1.7711 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.0262 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.5875 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | -0.6573 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.1482 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 3.2543 | `hold_sample` |
| `profit_band` | `profit_unknown` | 1664 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1373, 'bucket_count': 345, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'PYRAMID': 211, 'AVG_DOWN': 1162}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1191 | 1188 | None | -1.1654 | 0.1103 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 119 | 119 | None | -0.4442 | 0.4492 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 16 | 16 | None | -0.3444 | 0.6875 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 11 | 11 | None | -0.9209 | 0.2727 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3 | 2 | None | 0.47 | 1.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 33 | 2 | None | -3.41 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 835 | 835 | None | -1.1239 | 0.1425 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 317 | 317 | None | -1.0976 | 0.1577 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 158 | 154 | None | -1.0237 | 0.098 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 22 | 22 | None | -0.0564 | 0.7273 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 8 | 8 | None | -0.9125 | 0.0 | `hold_sample` |
| `ai_score_source` | `sim_scale_in_source_not_scored` | 3 | 2 | None | -3.41 | 0.0 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 30 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1162 | 1132 | None | -1.4021 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 211 | 206 | None | 0.648 | 0.9804 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1137 | 1107 | None | -1.3595 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 211 | 206 | None | 0.648 | 0.9804 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 25 | 25 | None | -3.2896 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 140 | 140 | None | 0.3584 | 0.9786 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 45 | 45 | None | -0.5709 | 0.2667 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 23, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.075 | -0.1 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.075 | -0.1 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.075 | -0.1 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | 0.2812 | 0.375 | 0.75 | `hold_sample` |

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
