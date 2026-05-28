# Lifecycle Decision Matrix - 2026-05-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-21`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `40873`
- source_rows_total: `40873`
- retained_rows: `40873`
- dropped_rows_by_source: `{}`
- joined_rows: `39098`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `23`
- entry_bucket_runtime_candidate_count: `7`
- holding_bucket_count/workorders: `25` / `10`
- exit_bucket_count/workorders: `74` / `10`
- scale_in_bucket_actionable_count: `207`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `59`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_submit': 23677, 'missing_holding': 23684, 'missing_exit': 23458, 'missing_entry': 22264}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1614 | 175 | -1.0141 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 198 | 180 | -1.011 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 191 | 180 | -0.6538 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 37865 | 37794 | -0.1592 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1005 | 769 | -0.5019 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 23875, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 40873, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 1614, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1605, 'exact_sim_record_id': 9}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 198, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 7, 'exact_sim_record_id': 191}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 191, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 191}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 37865, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 22055, 'exact_sim_record_id': 15810}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1005, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 769, 'candidate_id': 236}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_submit': 23677, 'missing_holding': 23684, 'missing_exit': 23458, 'missing_entry': 22264}, 'bucket_count': 59, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 21838 | 21817 | -0.1287 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 126 | 126 | -0.3994 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 477 | 96 | -0.9832 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9fa2e4711` | 476 | 29 | -1.0551 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 79 | 12 | -0.2638 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525` | 50 | 11 | -1.2365 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:442a1e9ce4` | 11 | 11 | -0.4727 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 11 | 11 | -0.3045 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:66ac2828ed` | 10 | 10 | -0.1 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:bf1dc11a14` | 20 | 9 | -0.7467 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 52 | 8 | -1.4359 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:2e49d5d51b` | 7 | 7 | -0.42 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:496a0a2877` | 29 | 3 | -1.4348 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:9c8589ac0c` | 3 | 3 | -0.4211 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:54077197b9` | 2 | 2 | -0.348 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:92dad7616b` | 7 | 2 | -0.6419 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 2 | 2 | -0.515 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c28a666880` | 2 | 2 | -0.2759 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c50ec68e5d` | 2 | 2 | 0.2201 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a32b91b4e5` | 3 | 1 | -1.8018 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1614, 'bucket_count': 131, 'actionable_bucket_count': 23, 'runtime_candidate_count': 7, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1440 | 174 | -0.9845 | -0.2668 | 0.4023 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 1 | -6.1601 | 5.57 | 1.0 | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `action_unknown` | 171 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 187 | 46 | -1.4571 | -0.1248 | 0.413 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 94 | 39 | -0.4221 | -0.0244 | 0.4615 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 75 | 12 | -0.718 | -0.5292 | 0.5 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 143 | 11 | -1.2279 | 0.2355 | 0.4545 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 153 | 8 | -1.4624 | -0.9825 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 15 | 6 | -1.3409 | -1.285 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 10 | 6 | 0.0235 | -0.9067 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 203 | 5 | -1.7949 | -0.6 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 21 | 4 | -0.1213 | -0.7575 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 5 | 4 | -1.9528 | -0.6625 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 43 | 3 | 0.2646 | -0.34 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 7 | 3 | -1.8733 | 1.7867 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 18 | 3 | -2.1678 | 0.56 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 6 | 3 | -0.5032 | 3.0033 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 23 | 3 | -0.36 | -1.47 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 8 | 2 | -2.0976 | -0.675 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 60 | 60 | -0.5081 | -0.2718 | 0.25 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 50 | 50 | -1.4996 | 1.6334 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 38 | 38 | -1.3468 | -1.855 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 15 | 15 | -0.6959 | -2.7427 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1614 | 175 | -1.0141 | -0.2335 | 0.4057 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 1387 | 175 | -1.0141 | -0.2335 | 0.4057 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 789 | 107 | -1.0297 | -0.2935 | 0.3925 | `candidate_tighten_or_exclude` |
| `score_band` | `score_lt60` | 698 | 44 | -0.8706 | -0.39 | 0.4318 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 82 | 12 | -1.2836 | 0.2517 | 0.3333 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 42 | 11 | -0.6742 | -0.0809 | 0.4545 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1215 | 174 | -0.9845 | -0.2668 | 0.4023 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 742 | 128 | -0.9209 | -0.1647 | 0.4141 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_unknown` | 571 | 30 | -1.2253 | -0.091 | 0.4667 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_block` | 81 | 10 | -1.2771 | -1.157 | 0.1 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 1216 | 175 | -1.0141 | -0.2335 | 0.4057 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 482 | 81 | -1.4082 | -0.2198 | 0.358 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 332 | 65 | -0.4539 | -0.2389 | 0.4462 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 479 | 21 | -1.4242 | -0.0452 | 0.4762 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_12`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `entry_bucket_16`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_17`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_21`: `time_bucket` / `time_1000_1200` -> `candidate_tighten_or_exclude`
- `entry_bucket_22`: `time_bucket` / `time_0900_1000` -> `candidate_tighten_or_exclude`
- `entry_bucket_23`: `time_bucket` / `time_1200_1400` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `scalp_sim_panic_lifecycle_full_exit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 198, 'bucket_count': 41, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 193 | 180 | -1.011 | `keep_collecting` |
| `actual_order_submitted` | `true` | 5 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 193 | 180 | -1.011 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 5 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 87 | 87 | -0.8084 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 80 | 80 | -1.0286 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 14 | 13 | -2.2582 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 10 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 5 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 198 | 180 | -1.011 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 198 | 180 | -1.011 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 198 | 180 | -1.011 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 198 | 180 | -1.011 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 197 | 180 | -1.011 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 198 | 180 | -1.011 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 158 | 158 | -0.9001 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 31 | 13 | -2.2582 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 8 | -1.3006 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | 0.0 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 156 | 156 | -0.9142 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 24 | 13 | -2.2582 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 11 | 11 | -0.9085 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 6 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `price_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 87 | 87 | -0.8084 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 80 | 80 | -1.0286 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 31 | 13 | -2.2582 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 167 | 167 | -0.9139 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 24 | 13 | -2.2582 | `keep_collecting` |
| `revalidation_state` | `block_False` | 7 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 167 | 167 | -0.9139 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 24 | 13 | -2.2582 | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 5 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `pre_submit_liquidity_guard_block` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 167 | 167 | -0.9139 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 21 | 13 | -2.2582 | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 191, 'source_row_count': 191, 'bucket_count': 25, 'joined_sample': 900, 'source_quality_adjusted_ev_pct': -0.6538, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 15, 'join_gap': 6, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 68 | 68 | -1.395 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 32 | 32 | -0.3665 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 27 | 27 | -0.3353 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 21 | 21 | -0.054 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 11 | 11 | 0.403 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 7 | 7 | 0.4741 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 5 | 5 | -1.6135 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 5 | 5 | -0.6254 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 2 | 2 | 2.0802 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 1 | 1 | -1.3978 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 1 | 1 | -0.2269 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_unknown|held=held_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 10 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 191 | 180 | -0.6538 | `source_quality_workorder` |
| `holding_action` | `WAIT` | 167 | 166 | -0.6568 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 23 | 13 | -0.5585 | `source_quality_workorder` |
| `holding_action` | `BUY` | 1 | 1 | -1.3978 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 191 | 180 | -0.6538 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 74 | 74 | -1.4098 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 33 | 33 | -0.3622 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 32 | 32 | -0.3806 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 21 | 21 | -0.054 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 11 | 11 | 0.403 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 0.831 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_unknown` | 11 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1005, 'source_row_count': 1005, 'bucket_count': 74, 'joined_sample': 3845, 'source_quality_adjusted_ev_pct': -0.5018, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 9, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 259 | 259 | -0.4478 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 172 | 172 | -1.0198 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 77 | 77 | 0.1877 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 32 | 32 | -0.3991 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 20 | 20 | -0.5674 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 15 | 15 | -2.1891 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 14 | 14 | -1.0043 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 13 | 13 | 1.1231 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 13 | 13 | -1.3505 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 11 | 11 | -1.2079 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.272 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 10 | 10 | -1.4952 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 8 | 8 | 0.2572 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.6607 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 7 | 7 | -0.894 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 7 | 7 | -0.58 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 6 | 6 | 1.9483 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 6 | 6 | 1.085 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 6 | 6 | 0.2395 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | 0.1001 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.0885 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 5 | 5 | -0.0123 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.5552 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 4 | 4 | -0.5664 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.3308 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.6577 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.7339 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.2572 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.5482 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.299 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | -0.0576 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 0.4249 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 3 | 3 | 0.7027 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.5728 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.433 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.2759 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8896 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -0.9037 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.2201 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | 0.4436 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 37865, 'bucket_count': 2549, 'actionable_bucket_count': 207, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 21965, 'PYRAMID': 90, 'arm_unknown': 15810}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 16703 | 16703 | -0.2012 | -0.227 | 0.3125 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 8015 | 8015 | -0.1628 | -0.1842 | 0.2659 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 6767 | 6767 | -0.0838 | -0.1085 | 0.3436 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 4980 | 4980 | -0.1529 | -0.1716 | 0.311 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 1329 | 1329 | -0.0181 | -0.0508 | 0.4454 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 71 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 37865 | 37794 | -0.1592 | -0.1832 | 0.3127 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 21965 | 21944 | -0.1675 | -0.2082 | 0.2822 | `hold_no_edge` |
| `arm` | `arm_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `arm` | `PYRAMID` | 90 | 40 | -16.6554 | -21.3597 | 0.75 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 19241 | 19232 | -0.138 | -0.1845 | 0.322 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2712 | 2712 | -0.3764 | -0.3764 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 58 | 40 | -16.6554 | -21.3597 | 0.75 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PRICE_GUARD` | 25 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 19 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `blocker_reason_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 5701 | 5701 | -0.0047 | -0.0721 | 0.4047 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 3698 | 3698 | -0.296 | -0.2947 | 0.1152 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 3409 | 3409 | -0.1647 | -0.2727 | 0.1297 | `hold_no_edge` |
| `blocker_reason` | `near_market_close` | 588 | 588 | -0.2298 | -0.2298 | 0.165 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 311 | 311 | -0.3178 | -0.3178 | 0.1061 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 306 | 306 | -0.3391 | -0.3391 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 125 | 125 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 99 | 99 | -0.07 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.09)` | 96 | 96 | 0.09 | 0.09 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.11)` | 88 | 88 | 0.11 | 0.11 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.13)` | 80 | 80 | 0.13 | 0.13 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.28)` | 75 | 75 | 0.28 | 0.28 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.08)` | 70 | 70 | 0.08 | 0.08 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.23)` | 69 | 69 | 0.23 | 0.23 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 68 | 68 | -0.05 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.01)` | 68 | 68 | 0.01 | 0.01 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 65 | 65 | -0.71 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 64 | 64 | -0.73 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.26)` | 60 | 60 | 0.26 | 0.26 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 58 | 58 | -0.95 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 56 | 56 | -0.72 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 52 | 52 | -0.09 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.12)` | 52 | 52 | 0.12 | 0.12 | 1.0 | `hold_no_edge` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `blocker_namespace` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_reason` / `scalping_cutoff` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(-0.73)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.95)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(-0.72)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(0.32)` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `scalping_cutoff` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-0.73)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.95)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(-0.72)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(0.32)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
