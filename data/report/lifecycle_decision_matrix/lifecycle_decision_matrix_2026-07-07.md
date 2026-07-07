# Lifecycle Decision Matrix - 2026-07-07

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-07`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4063`
- source_rows_total: `5534`
- retained_rows: `4063`
- dropped_rows_by_source: `{'dedupe': 1471}`
- joined_rows: `1359`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `1`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `25` / `5`
- exit_bucket_count/workorders: `40` / `10`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `67`
- lifecycle_flow_complete_count: `14`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `14` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0038`
- incomplete_flow_reason_counts: `{'missing_entry': 3596, 'postclose_exit_without_entry': 2337, 'missing_exit': 1372, 'missing_holding': 3681, 'missing_submit': 3659, 'candidate_id_only': 3588, 'scale_in_noise_only': 1254, 'sim_record_id_only': 27}`
- bucket_directed_sim_probe: `{'observed_row_count': 2488, 'matched_row_count': 0, 'background_row_count': 2488, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 146, 'not_instrumented': 2342}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 290 | 11 | -0.7494 | 0.0417 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 85 | 23 | -0.5869 | 0.6224 | `pass` | `NO_CHANGE` | False |
| `holding` | 54 | 23 | -1.342 | 0.9796 | `pass` | `EXIT` | False |
| `scale_in` | 1278 | 1253 | -0.8991 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2356 | 49 | -0.971 | 0.1019 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 3723, 'complete_flow_count': 14, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 14, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 27, 'direct_sim_record_incomplete_flow_count': 27, 'direct_sim_record_stage_coverage_counts': {'holding': 4, 'exit': 27}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 27, 'missing_submit': 27, 'sim_record_id_only': 27, 'postclose_exit_without_entry': 27, 'missing_holding': 23}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 3709, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 4063, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0038, 'complete_flow_conversion_denominator': 2356, 'complete_flow_conversion_rate': 0.0059, 'active_priority_incomplete_seed_count': 113, 'scale_in_followup_event_count': 1278, 'scale_in_unique_flow_count': 1199, 'scale_in_noise_flow_count': 1254, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 1254, 'active_priority_incomplete_seed_excluded': 113}, 'conversion_blocker_reason_counts': {'missing_entry': 2342, 'postclose_exit_without_entry': 2337, 'missing_holding': 2334, 'missing_exit': 5, 'missing_submit': 2334, 'sim_record_id_only': 27, 'candidate_id_only': 2307}, 'observation_seed_reason_counts': {'missing_exit': 1367, 'missing_holding': 1347, 'missing_submit': 1325, 'candidate_id_only': 1281, 'missing_entry': 1254, 'scale_in_noise_only': 1254}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 290, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 263, 'candidate_id': 27}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 85, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 85}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 54, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 50, 'exact_sim_record_id': 4}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 1278, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1254, 'exact_sim_record_id': 24}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 2356, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 18, 'exact_sim_record_id': 31, 'candidate_id': 2307}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 290, 'submit': 85, 'holding': 54, 'exit': 2356}, 'incomplete_flow_reason_counts': {'missing_entry': 3596, 'postclose_exit_without_entry': 2337, 'missing_exit': 1372, 'missing_holding': 3681, 'missing_submit': 3659, 'candidate_id_only': 3588, 'scale_in_noise_only': 1254, 'sim_record_id_only': 27}, 'bucket_count': 67, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:97cbb762ac` | 1 | 1 | -1.8301 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df2241cc71` | 1 | 1 | -1.9971 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f9a5c8b088` | 1 | 1 | 0.9854 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:55d6ebfa72` | 1 | 1 | -1.3083 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:13b06015fb` | 1 | 1 | -7.1358 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:341034850c` | 1 | 1 | -3.9421 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:0d9181453a` | 1 | 1 | -1.154 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:37777605a1` | 1 | 1 | 0.5255 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -1.7784 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:7cdbcbd798` | 1 | 1 | -1.616 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:79d3dd78b4` | 1 | 1 | -0.3379 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b288e033d2` | 1 | 1 | -3.5117 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bf30d2cd41` | 1 | 1 | -0.4267 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3aa984c653` | 1 | 1 | -2.0112 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1138 | 1121 | -1.1192 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 116 | 108 | 1.3345 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 18 | 18 | -0.9644 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 3 | 3 | 0.1008 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -0.56 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 2 | 2 | -2.4079 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 290, 'bucket_count': 130, 'actionable_bucket_count': 1, 'source_quality_blocked_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 1}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 22 | 6 | -0.7393 | -0.8035 | 0.5 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 228 | 5 | -0.7614 | -1.61 | 0.2 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 22 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 12 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 29 | 2 | 0.3351 | -3.41 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | -2.4079 | -2.9374 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | -1.0102 | -1.2607 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 1 | 1 | -1.7427 | 5.57 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 1 | 0.9797 | -3.56 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 1 | 1 | -3.7142 | -3.24 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 6 | 1 | 0.0773 | 1.02 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 1 | 2.3227 | 2.555 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_mid|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 4 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 216 | 10 | -0.832 | -1.3891 | 0.3 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `liquidity_bucket` / `liquidity_high` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 85, 'bucket_count': 83, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 19, 'refresh_applied_count': 18, 'still_latency_blocked_after_refresh_count': 1, 'latency_pass_recovered_count': 11, 'order_bundle_submitted_after_refresh_count': 10, 'refresh_subreason_counts': {'ws_snapshot_refresh_failed_missing': 1}, 'refresh_block_subreason_counts': {'ws_snapshot_refresh_failed_missing': 1}, 'latency_pass_recovered_downstream_counts': {'armed_expired_before_submit': 1, 'order_bundle_submitted': 10}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_not_attempted_or_not_instrumented': 31, 'refresh_not_attempted_or_not_needed': 1, 'refresh_resolved_quote_freshness': 3, 'sim_submit_path_not_applicable': 50}, 'pre_submit_refresh_applied_counts': {'refresh_not_attempted_or_not_instrumented': 32, 'sim_submit_path_not_applicable': 50, 'ws_snapshot_refresh_applied': 3}, 'real_submitted_row_count': 31, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 54 | 23 | -0.5869 | `keep_collecting` |
| `actual_order_submitted` | `true` | 31 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 54 | 23 | -0.5869 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 31 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 17 | 5 | -0.8168 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 13 | 3 | 0.7703 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 5 | -1.4849 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | -1.3914 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 3 | 0.2015 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_needed|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -1.7427 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.221 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 2.1813 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 50 | 23 | -0.5869 | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 16 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 15 | 0 | None | `keep_collecting` |
| `latency_reason` | `other_danger` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 50 | 23 | -0.5869 | `keep_collecting` |
| `latency_state` | `caution` | 16 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 16 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 3 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 35 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 35 | 12 | -0.2426 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 15 | 11 | -0.9625 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 35 | 12 | -0.2426 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 15 | 11 | -0.9625 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 43 | 17 | -0.8684 | `keep_collecting` |
| `overbought_bucket` | `overbought_not_available` | 35 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 7 | 6 | 0.2107 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 50 | 23 | -0.5869 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 35 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 54, 'source_row_count': 54, 'bucket_count': 25, 'joined_sample': 115, 'source_quality_adjusted_ev_pct': -1.342, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 15 | 15 | -2.2582 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.0938 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.4063 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.0327 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 50 | 23 | -1.342 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 48 | 22 | -1.3836 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 50 | 23 | -1.342 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 17 | 15 | -2.2582 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.0797 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.3 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 1.4063 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.0327 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |

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
- summary: `{'exit_rows': 2356, 'source_row_count': 2356, 'bucket_count': 40, 'joined_sample': 245, 'source_quality_adjusted_ev_pct': -0.971, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 18 | 18 | -1.1794 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.5114 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.3949 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.589 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.8475 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.225 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.0399 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -0.3823 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.4063 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.44 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.666 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.8301 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.5255 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.0327 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 38 | 0 | None | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 2269 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 27 | 27 | -0.7298 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 10 | 10 | -1.8609 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -0.6418 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2311 | 4 | -0.5363 | `source_quality_workorder` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | -1.3033 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 27 | 27 | -0.7298 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 9 | 9 | -1.8252 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | 0.601 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.5363 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 3 | 3 | -4.3027 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_rule_unknown` | 2307 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 27 | 27 | -0.7298 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 18 | 18 | -1.4293 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.5363 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 38 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2269 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 32 | 32 | -1.6331 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 9 | -0.4478 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.0797 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 2.4929 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.44 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.0327 | `hold_sample` |
| `profit_band` | `profit_unknown` | 2307 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_panic_context_warning|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `exit_outcome` / `GOOD_EXIT` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 1278, 'bucket_count': 285, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 1160, 'PYRAMID': 118}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1199 | 1192 | None | -1.1084 | 0.073 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 44 | 43 | None | 0.3674 | 0.4651 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 9 | 9 | None | -0.8889 | 0.1111 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 7 | 7 | None | -1.5114 | 0.2857 | `hold_sample` |
| `ai_score_band` | `score_70p` | 2 | 2 | None | -1.185 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 17 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 584 | 584 | None | -0.9363 | 0.0942 | `hold_sample` |
| `ai_score_source` | `live` | 567 | 567 | None | -1.216 | 0.0811 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 97 | 89 | None | -0.8864 | 0.0337 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 9 | 9 | None | -1.0622 | 0.4444 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 4 | 4 | None | -0.3975 | 0.5 | `hold_sample` |
| `ai_score_source` | `stage_rule_backfilled` | 17 | 0 | None | None | None | `hold_sample` |
| `arm` | `AVG_DOWN` | 1160 | 1143 | None | -1.2872 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 118 | 110 | None | 1.3175 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1138 | 1121 | None | -1.2496 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 118 | 110 | None | 1.3175 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 22 | 22 | None | -3.2036 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 43 | 43 | None | -1.08 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 42 | 42 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.64)` | 36 | 36 | None | -0.64 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 8, 'bucket_count': 19, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 4, 'SELL_TODAY': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.5363 | -0.715 | 0.0 | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |

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
