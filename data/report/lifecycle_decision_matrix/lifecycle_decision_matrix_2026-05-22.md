# Lifecycle Decision Matrix - 2026-05-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-22`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `35193`
- source_rows_total: `35193`
- retained_rows: `35193`
- dropped_rows_by_source: `{}`
- joined_rows: `33596`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `10`
- entry_bucket_runtime_candidate_count: `3`
- holding_bucket_count/workorders: `27` / `10`
- exit_bucket_count/workorders: `74` / `10`
- scale_in_bucket_actionable_count: `118`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `60`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 21259, 'missing_holding': 21263, 'missing_exit': 21106, 'missing_entry': 19960}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1486 | 102 | -0.3299 | 0.7001 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 129 | 123 | -0.2676 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 145 | 123 | -0.4473 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 32811 | 32785 | -0.159 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 622 | 463 | -0.428 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 21388, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 35193, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 1486, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1483, 'exact_sim_record_id': 3}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 129, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 4, 'exact_sim_record_id': 125}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 145, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 145}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 32811, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 19704, 'exact_sim_record_id': 13107}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 622, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 463, 'candidate_id': 159}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_submit': 21259, 'missing_holding': 21263, 'missing_exit': 21106, 'missing_entry': 19960}, 'bucket_count': 60, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14658 | 14645 | -0.3317 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5016 | 5015 | 0.3409 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 97 | 97 | -0.4457 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 444 | 59 | -0.3597 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9fa2e4711` | 397 | 13 | -0.0714 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 85 | 12 | -0.231 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525` | 39 | 7 | -0.4669 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:442a1e9ce4` | 5 | 5 | -0.47 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 41 | 3 | 0.9136 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 3 | 3 | 0.5367 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:bf1dc11a14` | 14 | 2 | -1.1512 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968` | 5 | 2 | -1.0532 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:293bde7f80` | 2 | 2 | -0.0037 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b0fe5e86f5` | 2 | 2 | -0.637 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:8312fd96fa` | 2 | 2 | 1.0697 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c28a666880` | 2 | 2 | -0.3699 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:496a0a2877` | 21 | 1 | 0.2454 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:ca25ee781d` | 4 | 1 | -0.3456 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:89265448ce` | 1 | 1 | -0.7257 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:54077197b9` | 1 | 1 | -2.9595 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1486, 'bucket_count': 135, 'actionable_bucket_count': 10, 'runtime_candidate_count': 3, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1297 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 4 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `action_unknown` | 183 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 88 | 36 | -0.128 | -0.6519 | 0.3889 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 168 | 20 | -0.7489 | -0.9905 | 0.3 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 71 | 11 | 0.263 | -0.7627 | 0.3636 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 21 | 9 | 0.1094 | -0.4356 | 0.5556 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 4 | 3 | -0.0865 | -0.17 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 19 | 3 | -1.3365 | -1.8367 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 35 | 3 | -1.2521 | -0.4167 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 142 | 2 | -0.5602 | -0.76 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 11 | 2 | 0.0426 | -1.665 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 7 | 2 | -1.1512 | -0.74 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 124 | 2 | -1.9108 | -0.53 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 46 | 1 | -0.5192 | 1.55 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 6 | 1 | 2.6555 | 1.64 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 3 | 1 | 0.2454 | 4.65 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 12 | 1 | 1.0009 | -1.63 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 34 | 34 | -0.3781 | 1.6615 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 29 | 29 | -0.2904 | -1.9386 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 23 | 23 | -0.4198 | -2.9513 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1486 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 1249 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 700 | 63 | -0.2895 | -0.6395 | 0.381 | `hold_no_edge` |
| `score_band` | `score_lt60` | 640 | 27 | -0.2151 | -0.5867 | 0.4444 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1065 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 700 | 80 | -0.3696 | -0.7194 | 0.3875 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_unknown` | 496 | 13 | -0.0714 | -0.7269 | 0.3846 | `hold_no_edge` |
| `strength_bucket` | `risk_unknown` | 1066 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 330 | 63 | 0.0438 | -0.5683 | 0.4286 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 418 | 33 | -0.8942 | -1.0012 | 0.2727 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_8`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_10`: `time_bucket` / `time_1000_1200` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `stale_bucket` / `fresh` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `strength_bucket` / `risk_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `time_bucket` / `time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 129, 'bucket_count': 36, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 129 | 123 | -0.2676 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 129 | 123 | -0.2676 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 71 | 71 | -0.2481 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 46 | 46 | -0.1881 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 6 | 6 | -1.1075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 3 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 2 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 129 | 123 | -0.2676 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 129 | 123 | -0.2676 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 129 | 123 | -0.2676 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 129 | 123 | -0.2676 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 128 | 123 | -0.2676 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 129 | 123 | -0.2676 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 115 | 115 | -0.226 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 12 | 6 | -1.1075 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 2 | -0.1369 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 114 | 114 | -0.1967 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 8 | 6 | -1.1075 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_limit` | 3 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 3 | 3 | -1.2819 | `keep_collecting` |
| `price_resolution_bucket` | `price_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 71 | 71 | -0.2481 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 46 | 46 | -0.1881 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 12 | 6 | -1.1075 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 117 | 117 | -0.2245 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 8 | 6 | -1.1075 | `keep_collecting` |
| `revalidation_state` | `block_False` | 4 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 117 | 117 | -0.2245 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 8 | 6 | -1.1075 | `keep_collecting` |
| `submit_source_stage` | `pre_submit_liquidity_guard_block` | 3 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 117 | 117 | -0.2245 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 10 | 6 | -1.1075 | `keep_collecting` |
| `would_limit_fill` | `true` | 2 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 145, 'source_row_count': 145, 'bucket_count': 27, 'joined_sample': 615, 'source_quality_adjusted_ev_pct': -0.4473, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 12, 'join_gap': 8, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 59 | 59 | -1.263 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 24 | 24 | -0.0733 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 14 | 14 | 0.2522 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 11 | 11 | 1.3503 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 9 | 9 | -0.3975 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 3 | 3 | 2.2712 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 1 | 1 | -3.23 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 1 | 1 | 2.3986 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 1 | 1 | 0.4685 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 12 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 125 | 123 | -0.4473 | `source_quality_workorder` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 120 | 120 | -0.4555 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 25 | 3 | -0.121 | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 125 | 123 | -0.4473 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 62 | 60 | -1.2958 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 36 | 24 | -0.0733 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 14 | 14 | 0.2522 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 12 | 12 | 1.2768 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 14 | 9 | -0.3975 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 4 | 2.303 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_unknown` | 2 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 622, 'source_row_count': 622, 'bucket_count': 74, 'joined_sample': 2315, 'source_quality_adjusted_ev_pct': -0.428, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 17, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 156 | 156 | -0.4597 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 100 | 100 | -1.1005 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 42 | 42 | 0.31 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.4224 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 12 | 12 | -1.7849 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 11 | 11 | -0.455 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 9 | 9 | 2.0978 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.9714 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | 0.1212 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.5633 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.106 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.4325 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | -0.7365 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | -0.1125 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 4 | 4 | 0.2008 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.1867 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | 0.0715 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.865 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.003 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -1.125 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.4143 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.3699 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.5749 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.3288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.3752 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.7576 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.3422 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_ai_review_exit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.4703 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.2009 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.6813 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.7587 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.1102 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 32811, 'bucket_count': 3507, 'actionable_bucket_count': 118, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 14670, 'PYRAMID': 5034, 'arm_unknown': 13107}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 14221 | 14221 | -0.2243 | -0.2707 | 0.2823 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 7362 | 7362 | -0.1144 | -0.1347 | 0.2651 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 5688 | 5688 | -0.0983 | -0.1312 | 0.2322 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 4578 | 4578 | -0.1259 | -0.1554 | 0.209 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 936 | 936 | -0.0474 | -0.0755 | 0.1966 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 26 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 32811 | 32785 | -0.159 | -0.1943 | 0.2571 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 14670 | 14657 | -0.3673 | -0.4275 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `arm` | `PYRAMID` | 5034 | 5021 | 0.2457 | 0.1828 | 0.8196 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN` | 9973 | 9960 | -0.4206 | -0.4807 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 5034 | 5021 | 0.2457 | 0.1828 | 0.8196 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4697 | 4697 | -0.2543 | -0.3147 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 3868 | 3868 | -0.1801 | -0.1904 | 0.12 | `hold_no_edge` |
| `blocker_reason` | `profit_not_enough` | 3633 | 3633 | 0.3993 | 0.3532 | 0.9408 | `candidate_recovery_or_relax` |
| `blocker_reason` | `near_market_close` | 1284 | 1284 | -0.073 | -0.073 | 0.1519 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 1028 | 1028 | -0.0265 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 555 | 555 | -0.027 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 532 | 532 | 0.0573 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 506 | 506 | -0.1376 | -0.1376 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 402 | 402 | -0.3394 | -0.3636 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 339 | 339 | -0.0604 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 335 | 335 | -0.6702 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 286 | 286 | -1.184 | -1.29 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 89 | 89 | -0.6967 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 87 | 87 | -0.0398 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 76 | 76 | -0.5846 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 73 | 73 | -0.7814 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 66 | 66 | -0.7168 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.12)` | 58 | 58 | -0.9965 | -1.12 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.28)` | 55 | 55 | -1.1711 | -1.28 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 47 | 47 | -0.6733 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 47 | 47 | -0.8356 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 46 | 46 | -1.094 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.24)` | 46 | 46 | -1.1417 | -1.24 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 44 | 44 | -12.4279 | -15.5639 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 44 | 44 | -1.0065 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 41 | 41 | -0.8017 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_4`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `pnl_out_of_range(-0.74)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-1.29)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `pnl_out_of_range(-0.74)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-1.29)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 60, 'bucket_count': 35, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 20, 'SELL_TODAY': 40}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | 3.34 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | 3.34 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 12 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 40 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 20 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 28 | 14 | -0.2121 | -0.2829 | 0.0 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.201 | 0.268 | 1.0 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 60 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 36 | 24 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 15 | 10 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 60 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `stage` | `exit` | 40 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |

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
