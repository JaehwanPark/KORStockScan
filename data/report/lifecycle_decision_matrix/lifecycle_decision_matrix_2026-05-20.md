# Lifecycle Decision Matrix - 2026-05-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-20`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `16634`
- source_rows_total: `16634`
- retained_rows: `16634`
- dropped_rows_by_source: `{}`
- joined_rows: `13910`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `19`
- entry_bucket_runtime_candidate_count: `5`
- holding_bucket_count/workorders: `19` / `10`
- exit_bucket_count/workorders: `60` / `10`
- scale_in_bucket_actionable_count: `106`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `64`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 10569, 'missing_holding': 10570, 'missing_exit': 10489, 'missing_entry': 9809}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1118 | 154 | -0.6889 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 239 | 238 | -0.6133 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 238 | 238 | -0.5938 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 14299 | 12621 | -0.1779 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 740 | 659 | -0.5419 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 10808, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 16634, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 1118, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1112, 'exact_sim_record_id': 6}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 239, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1, 'exact_sim_record_id': 238}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 238, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 238}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 14299, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 4795, 'candidate_id': 9504}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 740, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 659, 'candidate_id': 81}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_submit': 10569, 'missing_holding': 10570, 'missing_exit': 10489, 'missing_entry': 9809}, 'bucket_count': 64, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6136 | 6115 | -0.1836 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 3353 | 1702 | 0.1283 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 99 | 99 | -0.4863 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 231 | 88 | -0.598 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:66ac2828ed` | 33 | 33 | -0.3264 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 58 | 18 | -0.1617 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9fa2e4711` | 170 | 17 | -0.952 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c260e8fed9` | 16 | 16 | 0.3784 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:2e49d5d51b` | 15 | 15 | -0.434 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:1f8c274bdd` | 13 | 13 | -2.7862 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 24 | 12 | -2.0266 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:db291b2ff1` | 9 | 9 | -0.4248 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e29be7371d` | 8 | 8 | -1.7965 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525` | 25 | 7 | 0.1046 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:442a1e9ce4` | 6 | 6 | -0.4217 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:3e8349fb28` | 6 | 6 | -0.2934 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_unknown_source_:6fb94a6736` | 6 | 5 | -0.2387 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:92dad7616b` | 5 | 4 | -1.865 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:120416b9c4` | 4 | 4 | -0.5525 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:926cbbe021` | 4 | 4 | 2.6549 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1118, 'bucket_count': 118, 'actionable_bucket_count': 19, 'runtime_candidate_count': 5, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 639 | 147 | -0.6989 | -0.1869 | 0.3605 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 6 | 5 | -0.2387 | -1.3 | 0.2 | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 2 | 2 | -1.0775 | 0.485 | 0.5 | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `action_unknown` | 467 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 91 | 61 | -0.7377 | -0.1085 | 0.3443 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 40 | 27 | -0.2822 | -0.6463 | 0.4074 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 48 | 13 | -0.5692 | 0.38 | 0.4615 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 20 | 12 | -0.526 | -0.5983 | 0.25 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 13 | 11 | -2.1505 | -0.7455 | 0.1818 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 13 | 6 | 0.5668 | -0.3583 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 8 | 5 | -0.1224 | 0.594 | 0.6 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 5 | 4 | -1.865 | -1.21 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 32 | 4 | -2.1959 | 2.4575 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_unknown|source=scalp_sim_entry_ai_price_skip_order|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 4 | 4 | 0.1016 | -1.015 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 5 | 2 | 0.6721 | -0.57 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 1 | 1 | -0.6628 | -1.85 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 1 | 1 | 0.0184 | 4.21 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 1 | 1 | -1.5652 | 3.19 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 57 | 57 | -0.3585 | -0.4028 | 0.1579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 45 | 45 | -1.0363 | 2.2493 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 31 | 31 | -0.9597 | -1.8229 | 0.0323 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 20 | 20 | -0.4491 | -2.693 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1118 | 154 | -0.6889 | -0.2144 | 0.3571 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 997 | 154 | -0.6889 | -0.2144 | 0.3571 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 628 | 101 | -0.7616 | -0.2961 | 0.3465 | `candidate_tighten_or_exclude` |
| `score_band` | `score_lt60` | 370 | 39 | -0.6809 | 0.0154 | 0.3846 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 524 | 149 | -0.704 | -0.1779 | 0.3624 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 382 | 114 | -0.4944 | -0.2489 | 0.3684 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_unknown` | 227 | 22 | -0.7899 | 0.3759 | 0.4545 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_block` | 35 | 17 | -1.904 | -1.0065 | 0.1176 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 530 | 154 | -0.6889 | -0.2144 | 0.3571 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 195 | 105 | -0.8729 | -0.2123 | 0.3143 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 177 | 49 | -0.2947 | -0.2188 | 0.449 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_12`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `entry_bucket_14`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_15`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_19`: `time_bucket` / `time_1200_1400` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `scalp_sim_panic_lifecycle_full_exit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 239, 'bucket_count': 29, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 239 | 238 | -0.6133 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 239 | 238 | -0.6133 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 116 | 116 | -0.7394 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 105 | 105 | -0.537 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 17 | 17 | -0.2251 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 239 | 238 | -0.6133 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 239 | 238 | -0.6133 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 239 | 238 | -0.6133 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 239 | 238 | -0.6133 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 238 | 238 | -0.6133 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 239 | 238 | -0.6133 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 221 | 221 | -0.6432 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 18 | 17 | -0.2251 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 221 | 221 | -0.6432 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 17 | 17 | -0.2251 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 116 | 116 | -0.7394 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 105 | 105 | -0.537 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 18 | 17 | -0.2251 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 221 | 221 | -0.6432 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 17 | 17 | -0.2251 | `keep_collecting` |
| `revalidation_state` | `block_False` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 221 | 221 | -0.6432 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 17 | 17 | -0.2251 | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 221 | 221 | -0.6432 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 18 | 17 | -0.2251 | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 238, 'source_row_count': 238, 'bucket_count': 19, 'joined_sample': 1190, 'source_quality_adjusted_ev_pct': -0.5938, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 9, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 93 | 93 | -1.4354 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 74 | 74 | -0.2392 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 19 | 19 | -0.36 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 17 | 17 | 0.158 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 13 | 13 | 1.2487 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 13 | 13 | 0.542 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 7 | 7 | -1.4318 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_unknown` | 1 | 1 | 0.0135 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 1 | 1 | 0.7651 | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 238 | 238 | -0.5938 | `source_quality_workorder` |
| `holding_action` | `WAIT` | 229 | 229 | -0.5767 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 9 | 9 | -1.0271 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 238 | 238 | -0.5938 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 100 | 100 | -1.4351 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 74 | 74 | -0.2392 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 19 | 19 | -0.36 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 18 | 18 | 0.15 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 14 | 14 | 1.2141 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 13 | 13 | 0.542 | `candidate_recovery_or_relax` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 740, 'source_row_count': 740, 'bucket_count': 60, 'joined_sample': 3295, 'source_quality_adjusted_ev_pct': -0.5419, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 9, 'join_gap': 5, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 155 | 155 | -0.4608 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 116 | 116 | -1.0645 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 74 | 74 | -0.4088 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 53 | 53 | -0.1997 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 40 | 40 | 0.2208 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 20 | 20 | -2.6567 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 17 | 17 | -1.0065 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 17 | 17 | -1.7499 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -0.6307 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -0.917 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 11 | 11 | 0.1001 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 10 | 10 | -0.8218 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 10 | 10 | 0.0295 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 8 | 8 | 0.3387 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.865 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.5711 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 8 | 8 | -0.7376 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 8 | 8 | -0.4043 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 8 | 8 | 1.4074 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | 0.0242 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 0.8017 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 5 | 5 | 1.176 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.2426 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.5049 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 4 | 4 | 1.7175 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -1.2651 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -2.2417 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.1274 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 3 | 3 | 2.2502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 1.095 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -0.7132 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.1048 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.0739 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4064 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.5689 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | -1.7861 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.5514 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=exit_rule_unknown|outcome=outcome_unknown|profit=profit_unknown` | 81 | 0 | None | `source_quality_workorder` |
| `exit_outcome` | `outcome_unknown` | 502 | 421 | -0.5125 | `source_quality_workorder` |
| `exit_outcome` | `GOOD_EXIT` | 89 | 89 | -1.1648 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 14299, 'bucket_count': 979, 'actionable_bucket_count': 106, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 3374, 'AVG_DOWN': 6142, 'arm_unknown': 4783}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 3585 | 3585 | -0.0372 | -0.1024 | 0.3674 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 3436 | 3436 | -0.2094 | -0.2374 | 0.2264 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 2192 | 2192 | -0.1855 | -0.2335 | 0.292 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 2041 | 2041 | -0.4275 | -0.5213 | 0.3013 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1355 | 1355 | -0.097 | -0.1332 | 0.3048 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 1690 | 12 | 1.4747 | 1.3433 | 1.0 | `candidate_recovery_or_relax` |
| `ai_score_source` | `ai_source_unknown` | 14299 | 12621 | -0.1779 | -0.2316 | 0.2991 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 6142 | 6121 | -0.2263 | -0.2812 | 0.2625 | `hold_no_edge` |
| `arm` | `arm_unknown` | 4783 | 4783 | -0.1794 | -0.1765 | 0.3103 | `hold_no_edge` |
| `arm` | `PYRAMID` | 3374 | 1717 | -0.0011 | -0.2082 | 0.3984 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN` | 5294 | 5294 | -0.2019 | -0.2654 | 0.3036 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 4795 | 4795 | -0.1753 | -0.1727 | 0.312 | `hold_no_edge` |
| `blocker_namespace` | `PYRAMID` | 1705 | 1705 | -0.0115 | -0.2191 | 0.3941 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 827 | 827 | -0.3825 | -0.3825 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PRICE_GUARD` | 169 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 1509 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `blocker_reason_unknown` | 4795 | 4795 | -0.1753 | -0.1727 | 0.312 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 1780 | 1780 | -0.109 | -0.2155 | 0.3 | `hold_no_edge` |
| `blocker_reason` | `lifecycle_decision_matrix_pyramid` | 1510 | 1510 | -0.085 | -0.276 | 0.3437 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 1178 | 1178 | -0.2856 | -0.2856 | 0.163 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 619 | 619 | -0.1607 | -0.2679 | 0.1858 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 183 | 183 | -0.3445 | -0.3445 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 141 | 141 | 2.9679 | 3.072 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 38 | 38 | -0.07 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 35 | 35 | -0.05 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 30 | 30 | -0.109 | -0.1947 | 0.4 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 24 | 24 | -0.87 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.45)` | 24 | 24 | 0.45 | 0.45 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 21 | 21 | -0.8 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.01)` | 21 | 21 | 0.01 | 0.01 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.67)` | 21 | 21 | 0.67 | 0.67 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 20 | 20 | -0.76 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 19 | 19 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.14)` | 19 | 19 | 0.14 | 0.14 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 18 | 18 | -0.78 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 17 | 17 | -0.96 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.05)` | 17 | 17 | 0.05 | 0.05 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 16 | 16 | -0.08 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 16 | 16 | -0.84 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 16 | 16 | -0.9 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `scalping_pyramid_ok` -> `candidate_recovery_or_relax`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-0.87)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(0.45)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.80)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(0.67)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_reason` / `pnl_out_of_range(-0.78)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `scalping_pyramid_ok` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-0.87)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(0.45)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.80)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(0.67)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

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
