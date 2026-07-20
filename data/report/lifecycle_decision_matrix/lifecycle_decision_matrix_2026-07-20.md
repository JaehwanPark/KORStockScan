# Lifecycle Decision Matrix - 2026-07-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-20`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `410`
- source_rows_total: `1324`
- retained_rows: `410`
- dropped_rows_by_source: `{'dedupe': 914}`
- joined_rows: `66`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `16` / `0`
- exit_bucket_count/workorders: `28` / `5`
- scale_in_bucket_actionable_count: `0`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `30`
- lifecycle_flow_complete_count: `2`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `0` / `2` / `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0119`
- incomplete_flow_reason_counts: `{'missing_holding': 162, 'missing_exit': 150, 'missing_submit': 92, 'missing_entry': 69, 'postclose_exit_without_entry': 16, 'candidate_id_only': 67, 'scale_in_noise_only': 53, 'sim_record_id_only': 6}`
- bucket_directed_sim_probe: `{'observed_row_count': 43, 'matched_row_count': 0, 'background_row_count': 43, 'matched_unique_source_bucket_count': 0, 'match_status_counts': {'no_match': 25, 'not_instrumented': 16, 'policy_disabled': 2}, 'matched_classification_state_counts': {}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 248 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 81 | 3 | 0.3782 | 0.0111 | `hold_sample` | `ALLOW_SUBMIT` | False |
| `holding` | 8 | 3 | -0.2958 | 0.1125 | `hold_sample` | `EXIT` | False |
| `scale_in` | 53 | 53 | -0.4327 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 20 | 7 | -0.8243 | 0.245 | `hold_sample` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 168, 'complete_flow_count': 2, 'direct_sim_record_complete_flow_count': 0, 'adm_bridge_complete_flow_count': 2, 'fallback_complete_flow_count': 0, 'direct_flow_zero_diagnostic': {'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'direct_sim_record_flow_count': 6, 'direct_sim_record_incomplete_flow_count': 6, 'direct_sim_record_stage_coverage_counts': {'holding': 1, 'exit': 1}, 'direct_sim_record_incomplete_reason_counts': {'missing_entry': 6, 'missing_submit': 6, 'sim_record_id_only': 6, 'postclose_exit_without_entry': 1, 'missing_holding': 5, 'missing_exit': 5, 'scale_in_noise_only': 5}, 'runtime_effect': False, 'decision_authority': 'ldm_direct_flow_diagnostic_only'}, 'direct_flow_zero_reason': 'no_direct_complete_but_adm_bridge_complete', 'direct_flow_zero_closure_status': 'closed_by_adm_bridge_complete', 'direct_flow_zero_followup_required': False, 'incomplete_flow_count': 166, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 410, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0119, 'complete_flow_conversion_denominator': 18, 'complete_flow_conversion_rate': 0.1111, 'active_priority_incomplete_seed_count': 97, 'scale_in_followup_event_count': 53, 'scale_in_unique_flow_count': 50, 'scale_in_noise_flow_count': 53, 'denominator_exclusion_counts': {'scale_in_noise_flow_excluded': 53, 'active_priority_incomplete_seed_excluded': 97}, 'conversion_blocker_reason_counts': {'missing_entry': 16, 'postclose_exit_without_entry': 16, 'missing_submit': 14, 'sim_record_id_only': 1, 'missing_holding': 13, 'candidate_id_only': 13}, 'observation_seed_reason_counts': {'missing_holding': 149, 'missing_exit': 150, 'missing_submit': 78, 'missing_entry': 53, 'candidate_id_only': 54, 'scale_in_noise_only': 53, 'sim_record_id_only': 5}, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_holding', 'stage_identity': {'entry': {'source_row_count': 248, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 242, 'candidate_id': 6}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 81, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 81}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 8, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 7, 'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 53, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 48, 'exact_sim_record_id': 5}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 20, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 6, 'exact_sim_record_id': 1, 'candidate_id': 13}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 248, 'submit': 81, 'holding': 8, 'exit': 20}, 'incomplete_flow_reason_counts': {'missing_holding': 162, 'missing_exit': 150, 'missing_submit': 92, 'missing_entry': 69, 'postclose_exit_without_entry': 16, 'candidate_id_only': 67, 'scale_in_noise_only': 53, 'sim_record_id_only': 6}, 'bucket_count': 30, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3de51bc35d` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:a8a00e350f` | 1 | 1 | -1.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 37 | 37 | -1.0623 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 16 | 16 | 1.0232 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c6b7b772fb` | 1 | 1 | -1.63 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d0ed1aa56b` | 1 | 1 | 2.3727 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:12b48c8f43` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b58865037e` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:90c7bf43c5` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:4a1f1fe8a3` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 7 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:521ec1994f` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:18c5a6106d` | 2 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:932debda76` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6ed27efa34` | 1 | 0 | None | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 248, 'bucket_count': 76, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 16, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 6 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 12 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 56 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_STALE` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 169 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_state_normal|overbought=panic_entry_overbought_not_applicable|time=time_1200_1400` | 2 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1200_1400` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `exit_rule` / `exit_unknown` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `liquidity_bucket` / `liquidity_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `overbought_bucket` / `overbought_not_available` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `score_band` / `score_lt60` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 81, 'bucket_count': 92, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0, 'quote_freshness_attribution_present': True, 'row_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution_present': True, 'sentinel_quote_freshness_attribution': {'source_report_type': 'buy_funnel_sentinel', 'decision_authority': 'submit_drought_quote_freshness_attribution_only', 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['broker_order_submit', 'adm_ldm_training_input', 'general_threshold_ev_input', 'live_auto_promotion'], 'refresh_attempted_count': 75, 'refresh_applied_count': 63, 'still_latency_blocked_after_refresh_count': 10, 'latency_pass_recovered_count': 12, 'order_bundle_submitted_after_refresh_count': 5, 'refresh_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_invalid': 2, 'ws_snapshot_refresh_failed_stale': 9}, 'refresh_block_subreason_counts': {'observer_quote_refresh_failed_invalid': 1, 'observer_quote_refresh_failed_stale': 1, 'ws_snapshot_refresh_failed_invalid': 2, 'ws_snapshot_refresh_failed_stale': 9}, 'latency_pass_recovered_downstream_counts': {'order_bundle_submitted': 5, 'price_guard_or_revalidation': 7}, 'post_restart_window_policy': 'event_provenance_only'}, 'quote_freshness_resolution_counts': {'refresh_failed_quote_stale': 5, 'refresh_failed_source_unhealthy': 1, 'refresh_not_attempted_or_not_instrumented': 18, 'refresh_resolved_quote_freshness': 50, 'sim_submit_path_not_applicable': 7}, 'pre_submit_refresh_applied_counts': {'refresh_attempted_not_applied': 6, 'refresh_not_attempted_or_not_instrumented': 18, 'sim_submit_path_not_applicable': 7, 'ws_snapshot_refresh_applied': 50}, 'real_submitted_row_count': 18, 'missing_broker_order_key_count': 0, 'bot_history_broker_order_key_backfill_candidate_count': 0, 'bot_history_broker_order_key_backfill_full_coverage': False, 'bot_history_broker_order_key_exact_mapping_count': 0, 'bot_history_broker_order_key_exact_mapping_full_coverage': False, 'post_submit_provenance_join_resolution': 'no_gap_broker_order_key_present_or_no_missing_rows', 'bot_history_broker_order_key_backfill_candidates': [], 'missing_broker_order_key_rate': 0.0, 'post_submit_provenance_join_gap_raw': False, 'post_submit_provenance_join_gap': False}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 63 | 3 | 0.3782 | `keep_collecting` |
| `actual_order_submitted` | `true` | 18 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 63 | 3 | 0.3782 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 18 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 50 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -4.055 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_source_unhealthy|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_3_10s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=warning_observed_mark_gap_allowed|quote_age=quote_age_lt1s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=safe|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.0697 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `latency_reason` | `spread_above_caution_below_guard_cap` | 30 | 0 | None | `keep_collecting` |
| `latency_reason` | `spread_too_wide` | 16 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 7 | 3 | 0.3782 | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 6 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high,spread_too_wide` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `ws_age_too_high` | 4 | 0 | None | `keep_collecting` |
| `latency_reason` | `quote_stale,ws_age_too_high` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 60 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 8 | 0 | None | `keep_collecting` |
| `latency_state` | `simulated` | 7 | 3 | 0.3782 | `keep_collecting` |
| `latency_state` | `safe` | 6 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 74 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 6 | 3 | 0.3782 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 74 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 6 | 3 | 0.3782 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 8, 'source_row_count': 8, 'bucket_count': 16, 'joined_sample': 15, 'source_quality_adjusted_ev_pct': -0.2958, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.8651 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 7 | 3 | -0.2958 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 7 | 3 | -0.2958 | `hold_no_edge` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 7 | 3 | -0.2958 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -1.8651 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 20, 'source_row_count': 20, 'bucket_count': 28, 'joined_sample': 35, 'source_quality_adjusted_ev_pct': -0.8243, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 3 | 3 | -1.57 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.8651 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 6 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 7 | 0 | None | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 3 | 3 | -1.57 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 2 | 2 | 0.2538 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 1 | 1 | -1.395 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 13 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 3 | 3 | -1.57 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | 0.4889 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -1.8651 | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 6 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 7 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 3 | 3 | -1.57 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3 | 3 | -0.2958 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 6 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 7 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -1.6438 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 13 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `exit_outcome` / `outcome_not_applicable_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `exit_rule` / `scalp_sim_panic_lifecycle_partial_exit` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `exit_source_stage` / `scalp_sim_partial_sell_order_assumed_filled` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `profit_band` / `profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `incremental_notional_ev_pct`
- summary: `{'scale_in_rows': 53, 'bucket_count': 63, 'edge_bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_authority_blocked_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'arm_counts': {'AVG_DOWN': 37, 'PYRAMID': 16}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 52 | 52 | None | -0.6085 | 0.2885 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1 | 1 | None | 1.18 | 1.0 | `hold_sample` |
| `ai_score_source` | `live` | 27 | 27 | None | -0.8696 | 0.1111 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 16 | 16 | None | 0.3162 | 0.6875 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 8 | 8 | None | -1.595 | 0.125 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 2 | 2 | None | 0.36 | 0.5 | `hold_sample` |
| `arm` | `AVG_DOWN` | 37 | 37 | None | -1.2641 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 16 | 16 | None | 1.0194 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 37 | 37 | None | -1.2641 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 16 | 16 | None | 1.0194 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.21)` | 5 | 5 | None | -1.21 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 5 | 5 | None | 0.274 | 0.6 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 3 | 3 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 3 | 3 | None | -1.29 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 2 | 2 | None | -3.285 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 2 | 2 | None | -0.08 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.38)` | 2 | 2 | None | -0.38 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2 | 2 | None | 0.6 | 1.0 | `hold_sample` |
| `blocker_reason` | `rising_missed_scout_pyramid_bridge_blocked:profit_not_enough,quote_stale,micro_context_stale,tick_aggressor_pressure_unusable,fresh_micro_confirmation_missing,tick_accel_stale` | 2 | 2 | None | 0.13 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1 | 1 | None | -4.29 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 2, 'bucket_count': 15, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 1, 'SELL_TODAY': 1}}`

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
