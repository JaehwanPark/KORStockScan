# Lifecycle Decision Matrix - 2026-05-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-28`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `21807`
- source_rows_total: `21807`
- retained_rows: `21807`
- dropped_rows_by_source: `{}`
- joined_rows: `21144`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `13`
- entry_bucket_runtime_candidate_count: `4`
- scale_in_bucket_actionable_count: `192`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `66`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 500 | 91 | 1.3233 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 197 | 167 | -0.6543 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 183 | 167 | -0.8742 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 20128 | 20096 | -0.4519 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 799 | 623 | -0.7324 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 11515, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'bucket_count': 66, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8610 | 8587 | -0.6791 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2032 | 2023 | 0.6588 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 76 | 76 | -0.6624 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 49 | 49 | 1.643 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 42 | 42 | -0.5119 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 21 | 21 | 1.1823 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 16 | 16 | -0.4756 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 84 | 8 | 0.0085 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 8 | 8 | -0.61 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:f8ff028ae0` | 7 | 7 | 2.6634 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7ed5a2f0f0` | 7 | 7 | 0.3766 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 5 | 5 | -0.5836 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 17 | 4 | 0.2815 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 3 | 3 | -0.39 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:a1371ed802` | 3 | 3 | -1.102 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f67c8c8c9f` | 3 | 3 | 2.4445 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 2 | 2 | -0.47 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 2 | 2 | -0.415 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 2 | 2 | -0.33 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:938f2788bd` | 2 | 2 | -1.236 | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 500, 'bucket_count': 114, 'actionable_bucket_count': 13, 'runtime_candidate_count': 4, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `action_unknown` | 236 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 254 | 10 | -0.4688 | -0.847 | 0.4 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 6 | 4 | 0.2815 | -0.2275 | 0.5 | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.643 | 2.7405 | 0.5714 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 21 | 21 | 1.1823 | 1.9497 | 0.5714 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 7 | 7 | 2.6634 | 4.7435 | 0.7143 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 35 | 4 | -0.033 | -1.3875 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 26 | 3 | -0.4214 | 0.4933 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 11 | 3 | 0.2582 | 0.3 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_ok|time=time_1000_1200` | 2 | 1 | 1.4646 | 1.01 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_watch|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 4 | 1 | -1.0146 | -2.72 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 4 | 1 | 0.3513 | -1.81 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 7 | 1 | -3.742 | -2.69 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=ai_confirmed|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_0900_1000` | 30 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1000_1200` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_normal|time=time_1200_1400` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_0900_1000` | 10 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=blocked_ai_score|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_watch|time=time_1000_1200` | 4 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 486 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 500 | 91 | 1.3233 | 2.1874 | 0.5604 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 376 | 90 | 1.3217 | 2.2005 | 0.5556 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 156 | 53 | 1.5403 | 2.5165 | 0.566 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 25 | 21 | 1.1823 | 1.9497 | 0.5714 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 77 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 152 | 14 | -0.2545 | -0.67 | 0.4286 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 236 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 195 | 13 | -0.196 | -0.5123 | 0.4615 | `hold_no_edge` |
| `strength_bucket` | `strength_unknown` | 236 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |
| `strength_bucket` | `risk_unknown` | 152 | 14 | -0.2545 | -0.67 | 0.4286 | `hold_no_edge` |
| `time_bucket` | `time_unknown` | 236 | 77 | 1.6101 | 2.7069 | 0.5844 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_8`: `score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `entry_bucket_9`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_10`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_11`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `score_band` / `score_70p` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 197, 'bucket_count': 54, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 197 | 167 | -0.6543 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 196 | 167 | -0.6543 | `keep_collecting` |
| `broker_order_forbidden` | `false` | 1 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 106 | 96 | -0.5136 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 37 | 34 | -0.9861 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 14 | -0.5171 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 12 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -0.8524 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -2.0092 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 3 | 2 | 0.2353 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.7455 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.6658 | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_pass|revalidation=block_False|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_normal|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=pre_submit_liquidity_guard_block|revalidation=block_False|quote_age=quote_age_unknown|liquidity=below_min_liquidity|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.1792 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 183 | 167 | -0.6543 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `latency_state` | `simulated` | 183 | 167 | -0.6543 | `keep_collecting` |
| `latency_state` | `latency_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 162 | 148 | -0.7003 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 22 | 19 | -0.2956 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_unknown` | 13 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 161 | 148 | -0.7003 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 22 | 19 | -0.2956 | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 177 | 160 | -0.6284 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 13 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 7 | 7 | -1.2449 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 183 | 167 | -0.6543 | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 122 | 113 | -0.5859 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 51 | 45 | -0.8934 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 14 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 10 | 9 | -0.3166 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 111 | 103 | -0.5433 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 69 | 62 | -0.8673 | `keep_collecting` |
| `price_resolution_bucket` | `price_unknown` | 12 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 3 | 2 | 0.2353 | `source_quality_workorder` |
| `price_resolution_bucket` | `resolved_price` | 2 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 129 | 117 | -0.5578 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 20128, 'bucket_count': 1649, 'actionable_bucket_count': 192, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 2038, 'AVG_DOWN': 9208, 'arm_unknown': 8882}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 14653 | 14653 | -0.5066 | -0.5656 | 0.1879 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 2281 | 2281 | -0.396 | -0.446 | 0.2157 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 2004 | 2004 | -0.1183 | -0.1381 | 0.269 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 579 | 579 | -0.3357 | -0.3898 | 0.2591 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 578 | 578 | -0.5613 | -0.6112 | 0.1886 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 33 | 1 | 0.935 | 0.71 | 1.0 | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 20128 | 20096 | -0.4519 | -0.5056 | 0.2012 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 9208 | 9185 | -0.7239 | -0.8279 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 8882 | 8882 | -0.4242 | -0.4205 | 0.2314 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 2038 | 2029 | 0.6579 | 0.581 | 0.9803 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 8883 | 8883 | -0.424 | -0.4204 | 0.2315 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 6604 | 6581 | -0.8741 | -0.9885 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2604 | 2604 | -0.3442 | -0.422 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 2037 | 2028 | 0.6578 | 0.581 | 0.9803 | `candidate_recovery_or_relax` |
| `blocker_reason` | `blocker_reason_unknown` | 8883 | 8883 | -0.424 | -0.4204 | 0.2315 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 1771 | 1771 | -0.4703 | -0.5566 | 0.1666 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 1644 | 1644 | 0.605 | 0.524 | 0.983 | `candidate_recovery_or_relax` |
| `blocker_reason` | `low_broken` | 485 | 485 | -0.3647 | -0.3853 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 148 | 148 | -1.6261 | -2.0905 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 110 | 110 | -0.8464 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 106 | 106 | -0.968 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 105 | 105 | -0.6452 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 102 | 102 | -0.6974 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 95 | 95 | -0.9504 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 89 | 89 | -0.7616 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 86 | 86 | -0.0225 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 86 | 86 | -0.7492 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 78 | 78 | -0.8725 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 77 | 77 | -0.7571 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 67 | 67 | 2.8439 | 2.9042 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 64 | 64 | -0.834 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.21)` | 64 | 64 | -1.0884 | -1.21 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 63 | 63 | -1.1141 | -1.29 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 62 | 62 | -0.6458 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 61 | 61 | -0.0107 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 60 | 60 | -0.6919 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 60 | 60 | -1.2064 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 59 | 59 | -0.971 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 57 | 57 | -0.8234 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 56 | 56 | -0.6834 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_10`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_14`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `arm_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `blocker_namespace_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
