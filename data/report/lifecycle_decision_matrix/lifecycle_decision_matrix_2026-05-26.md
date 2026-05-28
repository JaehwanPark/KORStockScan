# Lifecycle Decision Matrix - 2026-05-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-26`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `48618`
- source_rows_total: `48618`
- retained_rows: `48618`
- dropped_rows_by_source: `{}`
- joined_rows: `47005`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `14`
- entry_bucket_runtime_candidate_count: `3`
- holding_bucket_count/workorders: `38` / `10`
- exit_bucket_count/workorders: `71` / `10`
- scale_in_bucket_actionable_count: `278`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `4`
- overnight_bucket_runtime_candidate_count: `2`
- lifecycle_flow_bucket_count: `74`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 25004, 'missing_holding': 25889, 'missing_exit': 25644, 'missing_submit': 25851}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1168 | 46 | -1.5688 | 0.1812 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 312 | 209 | -1.0091 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 297 | 209 | -0.8449 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 45601 | 45572 | -0.3171 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1240 | 969 | -0.5627 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 26163, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 48618, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 1168, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 1168}, 'identity_join_rate': 1.0}, 'submit': {'source_row_count': 312, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 38, 'exact_sim_record_id': 274}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 297, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 297}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 45601, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 25214, 'exact_sim_record_id': 20387}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 1240, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 969, 'candidate_id': 271}, 'identity_join_rate': 1.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 25004, 'missing_holding': 25889, 'missing_exit': 25644, 'missing_submit': 25851}, 'bucket_count': 74, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 19283 | 19276 | -0.588 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5138 | 5138 | 0.5465 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 92 | 92 | -0.4614 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 50 | 50 | -0.3966 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 50 | 50 | -0.4714 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 71 | 27 | -1.7249 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 14 | 14 | -0.3943 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 416 | 13 | -1.3009 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 12 | 12 | -0.1204 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 7 | 7 | -0.7686 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:34cc4a9d10` | 6 | 6 | -0.0462 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 6 | 6 | -0.5317 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 4 | 4 | -0.0875 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 92 | 3 | -1.8134 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b66960979a` | 3 | 3 | -0.1742 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 90 | 2 | -0.1321 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:70e9d883f8` | 2 | 2 | 0.7202 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7ed5a2f0f0` | 2 | 2 | -0.705 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d1e442c0e9` | 2 | 2 | 2.1444 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:1fb1ac6f78` | 5 | 2 | 0.8136 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1168, 'bucket_count': 164, 'actionable_bucket_count': 14, 'runtime_candidate_count': 3, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `BUY_NOW` | 38 | 26 | -1.7658 | -0.4092 | 0.4615 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 869 | 20 | -1.3126 | -1.0575 | 0.25 | `candidate_tighten_or_exclude` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 3 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `action_unknown` | 258 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 23 | 8 | -1.5671 | 1.12 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 21 | 7 | -1.2432 | -0.3671 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 122 | 6 | -0.4199 | -0.9417 | 0.1667 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 103 | 5 | -1.0886 | -1.384 | 0.2 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1400_close` | 5 | 3 | -3.2598 | -2.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 7 | 3 | -0.6957 | -1.77 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 34 | 2 | -2.088 | -2.395 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1000_1200` | 2 | 2 | -2.0667 | -0.81 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1200_1400` | 2 | 2 | -3.1601 | 0.39 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1000_1200` | 20 | 1 | -4.6766 | 0.49 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1200_1400` | 21 | 1 | -4.272 | -1.96 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 16 | 1 | -1.264 | -2.72 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_0900_1000` | 1 | 1 | -0.6489 | -2.9 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 6 | 1 | -2.3647 | 1.23 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 2 | 1 | -2.9755 | -2.05 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 29 | 1 | -0.9527 | 2.54 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 21 | 21 | -1.0755 | -1.8919 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 17 | 17 | -1.9702 | 1.6071 | 1.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1168 | 46 | -1.5688 | -0.6911 | 0.3696 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 909 | 36 | -1.1759 | -0.5383 | 0.3611 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 106 | 10 | -2.9831 | -1.241 | 0.4 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 232 | 28 | -1.7696 | -0.3814 | 0.4643 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 691 | 16 | -1.397 | -1.3469 | 0.1875 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 771 | 46 | -1.5688 | -0.6911 | 0.3696 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 725 | 42 | -1.5178 | -0.5293 | 0.4048 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 771 | 46 | -1.5688 | -0.6911 | 0.3696 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 314 | 19 | -1.4629 | 0.1405 | 0.4737 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 257 | 14 | -1.5436 | -1.45 | 0.2143 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `entry_bucket_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_11`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `BUY_NOW` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `scalp_soft_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_ok` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_60_62` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 312, 'bucket_count': 72, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 292 | 209 | -1.0091 | `keep_collecting` |
| `actual_order_submitted` | `true` | 20 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `true` | 292 | 209 | -1.0091 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 20 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 105 | 73 | -0.7277 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 54 | 37 | -0.1702 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 34 | 33 | -0.6121 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 17 | 17 | -3.0042 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 11 | -0.7812 | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=true` | 14 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 13 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -2.4966 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 12 | 9 | -1.4164 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=true` | 6 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -1.7565 | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_ok|latency=latency_unknown|fill=false|submitted=false` | 4 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=true|submitted=false` | 2 | 2 | -0.6135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.8802 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 1 | 1 | -0.6489 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.0648 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.0619 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -5.2406 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.23 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -4.7563 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 274 | 209 | -1.0091 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 38 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 274 | 209 | -1.0091 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 38 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 220 | 142 | -0.8875 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 71 | 67 | -1.2667 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 21 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 203 | 142 | -0.8875 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 71 | 67 | -1.2667 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 38 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 265 | 173 | -0.6632 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 42 | 32 | -2.7943 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 4 | 4 | -1.6867 | `keep_collecting` |
| `overbought_bucket` | `overbought_normal` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 297, 'source_row_count': 297, 'bucket_count': 38, 'joined_sample': 1045, 'source_quality_adjusted_ev_pct': -0.8449, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 19, 'join_gap': 15, 'missing_source_field': 2}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 67 | 67 | -1.7101 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 45 | 45 | -1.2907 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 21 | 21 | -0.4247 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 13 | 13 | -0.3415 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 13 | 13 | 0.4502 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 12 | 12 | -0.6412 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 10 | 10 | -0.2734 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 9 | 9 | -0.3488 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 8 | 8 | 1.3983 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 4 | 4 | 1.2624 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 3 | 3 | 0.8039 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 2 | 2 | -0.533 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 2 | 2 | -0.2168 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_unknown|held=held_unknown` | 3 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_unknown|held=held_unknown` | 49 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 13 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 5 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 9 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_600_1800s` | 1 | 0 | None | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 274 | 209 | -0.8449 | `source_quality_workorder` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 19 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_unknown` | 159 | 123 | -1.0733 | `source_quality_workorder` |
| `holding_action` | `WAIT` | 133 | 84 | -0.5179 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 5 | 2 | -0.533 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 274 | 209 | -0.8449 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 23 | 0 | None | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 119 | 114 | -1.5239 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 41 | 34 | -0.3928 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 26 | 25 | -0.0737 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 19 | 18 | 0.4696 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 20 | 11 | -0.3248 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 1.0659 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_unknown` | 65 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_6`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_7`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_8`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_9`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_10`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 1240, 'source_row_count': 1240, 'bucket_count': 71, 'joined_sample': 4845, 'source_quality_adjusted_ev_pct': -0.5627, 'source_quality_gate': 'pass', 'unknown_reason_counts': {'not_applicable': 16, 'join_gap': 8, 'missing_source_field': 1}, 'workorder_count': 10, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 358 | 358 | -0.471 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 250 | 250 | -1.1365 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 104 | 104 | 0.2642 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 21 | 21 | -1.6019 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 21 | 21 | -1.2791 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 20 | 20 | -1.8138 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 18 | 18 | -0.9936 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 17 | 17 | 1.1594 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 14 | 14 | -2.4868 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 12 | 12 | 2.035 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 9 | 9 | -0.2758 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 9 | 9 | -0.2758 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 9 | 9 | -0.6584 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 9 | 9 | -0.6888 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 8 | 8 | 0.0825 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.135 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.135 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 7 | 7 | -1.3815 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | -0.129 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -2.0322 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.6149 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 6 | 6 | 1.0616 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 6 | 6 | 0.2028 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.8025 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.8025 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.4298 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300_plus` | 3 | 3 | 4.088 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.1742 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.8023 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 0.1562 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | -0.1464 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.645 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 1 | 1 | 1.6425 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.645 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 1 | 1 | 1.6425 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | 0.3966 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.0663 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.3293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_protect_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.241 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_preset_tp_touch|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 2.4227 | `hold_sample` |

### Exit Bucket Attribution Workorders

- `exit_bucket_source_quality_1`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_2`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_3`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_4`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_5`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_6`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_7`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_8`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_9`: `combo_exit_result` / `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `exit_bucket_source_quality_10`: `combo_exit_result` / `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` -> `exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 45601, 'bucket_count': 4044, 'actionable_bucket_count': 278, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 19443, 'PYRAMID': 5771, 'arm_unknown': 20387}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 33112 | 33112 | -0.2839 | -0.324 | 0.2585 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 5223 | 5223 | -0.3253 | -0.365 | 0.2397 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 2891 | 2891 | -0.2435 | -0.2711 | 0.2383 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 2516 | 2516 | -0.8052 | -0.9548 | 0.2142 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 1830 | 1830 | -0.3409 | -0.382 | 0.241 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 29 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 45601 | 45572 | -0.3171 | -0.3625 | 0.2519 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 20387 | 20387 | -0.2559 | -0.2541 | 0.2863 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 19443 | 19436 | -0.6197 | -0.7067 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 5771 | 5749 | 0.4885 | 0.4166 | 0.9817 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 20387 | 20387 | -0.2559 | -0.2541 | 0.2863 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN` | 12328 | 12321 | -0.7722 | -0.8647 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 7115 | 7115 | -0.3555 | -0.4332 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 5771 | 5749 | 0.4885 | 0.4166 | 0.9817 | `candidate_recovery_or_relax` |
| `blocker_reason` | `blocker_reason_unknown` | 20387 | 20387 | -0.2559 | -0.2541 | 0.2863 | `hold_no_edge` |
| `blocker_reason` | `profit_not_enough` | 4709 | 4709 | 0.5589 | 0.5094 | 0.9862 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 4225 | 4225 | -0.2895 | -0.3021 | 0.1946 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 750 | 750 | -0.3482 | -0.3722 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 476 | 476 | -0.39 | -0.408 | 0.105 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 304 | 304 | -0.7259 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 231 | 231 | -0.6562 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 190 | 190 | -0.7097 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 171 | 171 | -0.8908 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 152 | 152 | -0.8108 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.17)` | 151 | 151 | -1.0322 | -1.17 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 147 | 147 | -0.8189 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 147 | 147 | -0.9323 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 144 | 144 | 0.0218 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 141 | 141 | -0.8708 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 137 | 137 | -1.0253 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.34)` | 135 | 135 | -1.1526 | -1.34 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 125 | 125 | -0.0352 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 123 | 123 | -0.0032 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.03)` | 123 | 123 | -0.909 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 120 | 120 | -0.7981 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 120 | 120 | 2.8918 | 2.9401 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-1.39)` | 119 | 119 | -1.2194 | -1.39 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 118 | 118 | -0.7422 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 114 | 114 | -0.6889 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 108 | 108 | -0.8057 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_7`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_11`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 69, 'bucket_count': 41, 'actionable_bucket_count': 4, 'runtime_candidate_count': 2, 'workorder_count': 4, 'status_counts': {'HOLD_OVERNIGHT': 23, 'SELL_TODAY': 46}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 9 | -0.2758 | -0.3678 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 9 | 9 | -0.2758 | -0.3678 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 7 | 7 | 0.135 | 0.18 | 0.7143 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.135 | 0.18 | 0.7143 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -0.8025 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 5 | 5 | -0.8025 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.645 | 0.86 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 1 | 1.6425 | 2.19 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.645 | 0.86 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300` | 1 | 1 | 1.6425 | 2.19 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 46 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 38 | 19 | -0.1851 | -0.2468 | 0.2632 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | 0.0638 | 0.085 | 0.5 | `hold_sample` |
| `overnight_action` | `SELL_TODAY` | 46 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 46 | 46 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `peak_profit_band` | `peak_unknown` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 32 | 16 | -0.4134 | -0.5513 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.213 | 0.284 | 1.0 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 69 | 46 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 27 | 18 | -0.2758 | -0.3678 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 21 | 14 | 0.135 | 0.18 | 0.7143 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 15 | 10 | -0.8025 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 69 | 46 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 23 | 23 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |
| `stage` | `exit` | 46 | 46 | -0.1418 | -0.1891 | 0.3043 | `hold_no_edge` |

### Overnight Bucket Runtime Approval Candidates

- `overnight_bucket_3`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`
- `overnight_bucket_4`: `profit_band` / `profit_lt_neg070` -> `candidate_tighten_or_exclude`

### Overnight Bucket Workorders

- `overnight_bucket_source_quality_1`: `combo_overnight_decision` / `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_2`: `combo_overnight_decision` / `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_3`: `peak_profit_band` / `peak_lt_zero` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `overnight_bucket_source_quality_4`: `profit_band` / `profit_lt_neg070` -> `overnight_decision_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
