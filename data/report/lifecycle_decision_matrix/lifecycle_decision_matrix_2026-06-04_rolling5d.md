# Lifecycle Decision Matrix - 2026-06-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-04_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2558`
- source_rows_total: `4116`
- retained_rows: `2558`
- dropped_rows_by_source: `{'dedupe': 1558}`
- joined_rows: `2417`
- policy_pass_count: `4`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `23` / `7`
- exit_bucket_count/workorders: `51` / `10`
- scale_in_bucket_actionable_count: `92`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `12`
- overnight_bucket_runtime_candidate_count: `9`
- lifecycle_flow_bucket_count: `62`
- lifecycle_flow_complete_count: `4`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0017`
- incomplete_flow_reason_counts: `{'missing_entry': 2240, 'missing_holding': 2275, 'missing_exit': 2167, 'missing_submit': 2282, 'postclose_exit_without_entry': 97, 'candidate_id_only': 2147, 'sim_record_id_only': 31}`
- bucket_directed_sim_probe: `{'observed_row_count': 125, 'matched_row_count': 42, 'background_row_count': 83, 'matched_unique_source_bucket_count': 2, 'match_status_counts': {'matched': 42, 'no_match': 22, 'not_instrumented': 61}, 'matched_classification_state_counts': {'lifecycle_flow_sim_probe_candidate': 42}, 'primary_source': 'matched_bucket_directed_sim_probe_only', 'background_source': 'unmatched_or_policy_missing_sim_observation', 'runtime_effect': False, 'actual_order_submitted': False, 'broker_order_forbidden': True}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `['clean_tuning_baseline_excluded_source_dates']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 102 | 4 | -1.404 | 0.0157 | `hold_sample` | `WAIT_REQUOTE` | False |
| `submit` | 25 | 11 | -0.6676 | 0.484 | `pass` | `NO_CHANGE` | False |
| `holding` | 29 | 11 | -0.9616 | 0.4172 | `pass` | `EXIT` | False |
| `scale_in` | 2154 | 2154 | -0.5457 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 248 | 237 | -0.948 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 2303, 'complete_flow_count': 4, 'incomplete_flow_count': 2299, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2558, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0017, 'join_contract_blocked': False, 'bundle_ev_tuning_state': 'ready_for_bundle_ev_tuning', 'top_incomplete_reason': 'missing_submit', 'stage_identity': {'entry': {'source_row_count': 102, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 89, 'candidate_id': 13}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 25, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 25}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 29, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 11, 'exact_sim_record_id': 18}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 2154, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 2123, 'exact_sim_record_id': 31}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 248, 'identity_missing_count': 0, 'identity_quality_counts': {'entry_adm_bridge_key': 205, 'exact_sim_record_id': 32, 'candidate_id': 11}, 'identity_join_rate': 1.0}}, 'required_stage_source_counts': {'entry': 102, 'submit': 25, 'holding': 29, 'exit': 248}, 'incomplete_flow_reason_counts': {'missing_entry': 2240, 'missing_holding': 2275, 'missing_exit': 2167, 'missing_submit': 2282, 'postclose_exit_without_entry': 97, 'candidate_id_only': 2147, 'sim_record_id_only': 31}, 'bucket_count': 62, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2cbcb88794` | 1 | 1 | -2.3322 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:489169b716` | 1 | 1 | -0.0516 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:07087b9bfb` | 1 | 1 | -2.185 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d6b15884e3` | 1 | 1 | -1.8239 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1871 | 1871 | -0.6765 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 261 | 261 | 0.4071 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:23320ac43e` | 5 | 5 | -0.1805 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ffa670224b` | 5 | 5 | 1.0715 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -0.854 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 5 | 5 | 2.2264 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:0562f02c36` | 4 | 4 | -0.8877 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.66 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 4 | 4 | -1.36 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dc71748efe` | 3 | 3 | -1.0929 | `hold_sample` | `join_contract_blocked` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:1222f9a339` | 3 | 3 | -1.18 | `hold_sample` | `join_contract_blocked` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 102, 'bucket_count': 66, 'actionable_bucket_count': 0, 'source_quality_blocked_bucket_count': 51, 'runtime_candidate_count': 0, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 2 | 2 | -2.0351 | -0.1878 | 0.0 | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 1 | 1 | 1.9968 | -2.1 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 86 | 1 | -3.5428 | -1.82 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 11 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | -4.18 | -0.3755 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1400_close` | 1 | 1 | 1.9968 | -2.1 | 0.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 1 | 1 | 0.1099 | 0.0 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=pullback_required|time=time_1400_close` | 1 | 1 | -3.5428 | -1.82 | 0.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1400_close` | 4 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1400_close` | 11 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_chase_risk|time=time_1400_close` | 1 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1400_close` | 1 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1400_close` | 1 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1400_close` | 4 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 18 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1400_close` | 2 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 3 | 0 | None | None | None | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 1 | 0 | None | None | None | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_unknown_source_quality_1`: `chosen_action` / `BUY_NOW` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_3`: `chosen_action` / `SKIP_SOURCE_QUALITY` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_4`: `combo_entry_spot` / `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=pullback_required|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_6`: `combo_entry_spot` / `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_7`: `combo_entry_spot` / `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_8`: `combo_entry_spot` / `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_chase_risk|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_9`: `combo_entry_spot` / `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`
- `entry_bucket_unknown_source_quality_10`: `combo_entry_spot` / `score=score_60_62|source=blocked_ai_score|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1400_close` -> `unknown_bucket_source_quality_blocker`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 25, 'bucket_count': 55, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 24 | 11 | -0.6676 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 20 | 11 | -0.6676 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 5 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.324 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.58 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 2 | 2 | -0.935 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.4651 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.574 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.87 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 11 | 11 | -0.6676 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 11 | 11 | -0.6676 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 12 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 8 | 6 | -0.7502 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 5 | 5 | -0.5684 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 6 | 6 | -0.7502 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 5 | 5 | -0.5684 | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 11 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 7 | 7 | -0.5117 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 4 | -0.9403 | `keep_collecting` |
| `overbought_bucket` | `overbought_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 11 | 11 | -0.6676 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 7 | 7 | -0.9155 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 4 | 4 | -0.2336 | `keep_collecting` |
| `price_resolution_bucket` | `price_unknown` | 7 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 5 | 5 | -0.9078 | `keep_collecting` |
| `price_resolution_bucket` | `resolved_price` | 4 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 3 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 3 | 3 | -0.5028 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 2 | 2 | -0.935 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 1 | 1 | 0.574 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 29, 'source_row_count': 29, 'bucket_count': 23, 'joined_sample': 55, 'source_quality_adjusted_ev_pct': -0.9616, 'source_quality_gate': 'pass', 'unknown_reason_counts': {}, 'workorder_count': 7, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.1969 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -1.0922 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.05 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.17 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 11 | 11 | -0.9616 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 8 | 8 | -0.9127 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 3 | -1.0922 | `candidate_tighten_or_exclude` |
| `holding_action` | `SELL_TODAY` | 18 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 11 | 11 | -0.9616 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 18 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -1.162 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 1 | 0.05 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 1 | -0.17 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `WAIT` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `holding_action` / `holding_action_not_applicable_at_start` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `holding_source_stage` / `scalp_sim_holding_started` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 248, 'source_row_count': 248, 'bucket_count': 51, 'joined_sample': 1185, 'source_quality_adjusted_ev_pct': -0.948, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 4, 'join_gap': 5, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 35 | 35 | -0.9874 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 34 | 34 | -1.9659 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 32 | 32 | -1.3066 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 27 | 27 | -1.0127 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.2291 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 12 | 12 | -0.4258 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 9 | 9 | -0.9142 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 7 | 7 | -1.3157 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.5486 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 7 | 7 | 1.0747 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.2838 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 6 | 6 | -0.8186 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 6 | 6 | 0.5474 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.3955 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -1.5332 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.0514 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.9543 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 2.6015 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 2 | 2 | 0.1837 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.3629 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 1.0425 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_bad_entry_refined_canary|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -0.9064 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.6367 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.0155 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.3141 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 0.4773 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `MISSED_UPSIDE` | 83 | 83 | -0.4598 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 76 | 76 | -1.5754 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 46 | 46 | -0.9831 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 29 | 18 | -0.4733 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 14 | 14 | -0.9321 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 101 | 101 | -1.4179 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 51 | 51 | 0.3242 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 49 | 49 | -1.502 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.4733 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 14 | 14 | -0.9321 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -0.6451 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_bad_entry_refined_canary` | 1 | 1 | -0.9064 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 11 | 0 | None | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 2154, 'bucket_count': 546, 'actionable_bucket_count': 92, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 1891, 'PYRAMID': 263}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 1918 | 1918 | -0.5545 | -0.5923 | 0.1152 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 132 | 132 | -0.5179 | -0.5587 | 0.2197 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 82 | 82 | -0.3491 | -0.3817 | 0.1585 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 16 | 16 | -0.3945 | -0.405 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 6 | 6 | -1.434 | -1.5267 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 2154 | 2154 | -0.5457 | -0.5834 | 0.1221 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 1891 | 1891 | -0.6781 | -0.718 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 263 | 263 | 0.4064 | 0.3839 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN` | 1333 | 1333 | -0.8052 | -0.8463 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 558 | 558 | -0.3744 | -0.4115 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 263 | 263 | 0.4064 | 0.3839 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 277 | 277 | -0.3954 | -0.3973 | 0.0975 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 212 | 212 | 0.3779 | 0.3561 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_cutoff` | 148 | 148 | -0.382 | -0.3916 | 0.0743 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 43 | 43 | -1.0432 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 37 | 37 | -0.8988 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 36 | 36 | -0.4313 | -0.4544 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 31 | 31 | -0.7026 | -0.7026 | 0.0968 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 30 | 30 | -0.9078 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 29 | 29 | -0.058 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.48)` | 29 | 29 | -1.4194 | -1.48 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 28 | 28 | -0.7496 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 28 | 28 | -0.9092 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 27 | 27 | -0.7227 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 25 | 25 | -1.2159 | -1.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.17)` | 24 | 24 | -1.101 | -1.17 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.44)` | 22 | 22 | -1.3758 | -1.44 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 21 | 21 | -0.8475 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 20 | 20 | -0.8102 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 20 | 20 | -1.0228 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 19 | 19 | -0.6847 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.26)` | 18 | 18 | -1.206 | -1.26 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 18 | 18 | -1.2807 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 16 | 16 | -1.0761 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 15 | 15 | -0.6524 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 15 | 15 | -0.9399 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 15 | 15 | -0.9613 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.35)` | 15 | 15 | -1.2716 | -1.35 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.83)` | 14 | 14 | -0.7877 | -0.83 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 14 | 14 | -0.93 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `ai_score_source` / `score_field_backfilled` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_9`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `ai_score_source` / `score_field_backfilled` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 36, 'bucket_count': 27, 'actionable_bucket_count': 12, 'runtime_candidate_count': 9, 'workorder_count': 10, 'status_counts': {'HOLD_OVERNIGHT': 18, 'SELL_TODAY': 18}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -0.9142 | -1.2189 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.2838 | -0.3783 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.1837 | 0.245 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 1.0425 | 1.39 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 36 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 13 | -0.4327 | -0.5769 | 0.1538 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.579 | -0.772 | 0.2 | `candidate_tighten_or_exclude` |
| `overnight_action` | `SELL_TODAY` | 36 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 18 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `overnight_status` | `HOLD_OVERNIGHT` | 18 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 30 | 15 | -0.662 | -0.8827 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.1837 | 0.245 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 1.0425 | 1.39 | 1.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 36 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -0.9142 | -1.2189 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.2838 | -0.3783 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 36 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 18 | 18 | -0.4733 | -0.6311 | 0.1667 | `candidate_tighten_or_exclude` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_2`: `confidence_band` / `confidence_070p` -> `candidate_tighten_or_exclude`
- `overnight_bucket_3`: `held_bucket` / `held_600_1800s_plus` -> `candidate_tighten_or_exclude`
- `overnight_bucket_5`: `overnight_action` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_6`: `overnight_status` / `SELL_TODAY` -> `candidate_tighten_or_exclude`
- `overnight_bucket_7`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_8`: `price_source` / `holding_price_samples_last` -> `candidate_tighten_or_exclude`
- `overnight_bucket_10`: `source_quality_gate` / `overnight_decision_coverage` -> `candidate_tighten_or_exclude`
- `overnight_bucket_11`: `source_stage` / `scalp_sim_overnight_sell_today` -> `candidate_tighten_or_exclude`
- `overnight_bucket_12`: `stage` / `exit` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `confidence_band` / `confidence_070p` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `held_bucket` / `held_600_1800s_plus` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `held_bucket` / `held_600_1800s` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_5`: `overnight_action` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_6`: `overnight_status` / `SELL_TODAY` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_7`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_8`: `price_source` / `holding_price_samples_last` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_9`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_10`: `source_quality_gate` / `overnight_decision_coverage` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
