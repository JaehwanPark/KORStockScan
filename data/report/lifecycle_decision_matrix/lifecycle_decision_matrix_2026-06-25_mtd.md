# Lifecycle Decision Matrix - 2026-06-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-25_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `238149`
- source_rows_total: `349133`
- retained_rows: `238149`
- dropped_rows_by_source: `{}`
- joined_rows: `210735`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `None`
- entry_bucket_runtime_candidate_count: `None`
- holding_bucket_count/workorders: `None` / `None`
- exit_bucket_count/workorders: `None` / `None`
- scale_in_bucket_actionable_count: `None`
- scale_in_bucket_runtime_candidate_count: `None`
- overnight_bucket_actionable_count: `None`
- overnight_bucket_runtime_candidate_count: `None`
- lifecycle_flow_bucket_count: `965`
- lifecycle_flow_complete_count: `1231`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0057`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 13942 | 1923 | 0.7421 | 0.9581 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4719 | 3102 | -0.5217 | 0.9982 | `pass` | `NO_CHANGE` | False |
| `holding` | 4458 | 3102 | -0.9508 | 0.9979 | `pass` | `EXIT` | False |
| `scale_in` | 199331 | 196982 | -0.4348 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 15699 | 5626 | -0.9443 | 0.9952 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 965, 'complete_flow_count': 1231, 'incomplete_flow_count': 214888, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 154323 | 153598 | -0.73 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 42568 | 40944 | 0.694 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 2017 | 2017 | -1.0424 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 450 | 450 | 1.5294 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 359 | 359 | 1.7199 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 226 | 226 | 1.7128 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 176 | 176 | -0.2017 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 66 | 66 | -0.9379 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 38 | 38 | -0.8637 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 30 | 30 | -1.0348 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 24 | 24 | -1.9926 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 18 | 18 | -0.9387 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 16 | 16 | -0.5901 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 15 | 15 | -0.8227 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 15 | 15 | -0.8072 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 14 | 14 | -1.367 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 13 | 13 | -1.0217 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 555, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 9600 | 1914 | 0.7427 | 0.8433 | 0.4598 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 9159 | 1438 | 0.6009 | 0.3064 | 0.4388 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 1042 | 1042 | 1.6315 | 2.6182 | 0.6478 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 13061 | 1042 | 1.6315 | 2.6182 | 0.6478 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 9971 | 805 | -0.3035 | -1.2944 | 0.2323 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 795 | 795 | 1.398 | 2.2732 | 0.6264 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 2820 | 718 | 1.3703 | 2.2314 | 0.6323 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6301 | 710 | -0.3131 | -1.3312 | 0.2225 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 6316 | 673 | 0.0369 | -0.7179 | 0.2897 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1463 | 658 | 1.1569 | 1.7779 | 0.5836 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5639 | 608 | -0.2948 | -1.2735 | 0.2319 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2992 | 519 | 0.6821 | 0.7713 | 0.4894 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1339 | 486 | 0.9965 | 1.5683 | 0.5658 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 6275 | 429 | -0.3291 | -1.4402 | 0.2005 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 427 | 427 | -0.23 | -1.9816 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2454 | 392 | 0.4874 | 0.2624 | 0.4031 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 596 | 305 | 1.3755 | 2.0946 | 0.5901 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1405 | 258 | 1.0966 | 1.7084 | 0.5078 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 1027 | 232 | 0.849 | 1.2431 | 0.5 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 220 | 220 | -0.2696 | -3.0048 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1757 | 216 | 0.3277 | 0.3824 | 0.3657 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 200 | 200 | -0.5231 | 2.0207 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 113 | 113 | 1.0841 | 1.4296 | 0.6372 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 189, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4570 | 3102 | -0.5217 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 4184 | 3102 | -0.5217 | `keep_collecting` |
| `latency_state` | `simulated` | 4184 | 3102 | -0.5217 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4553 | 3102 | -0.5217 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4135 | 3067 | -0.5077 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3894 | 2902 | -0.539 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3560 | 2633 | -0.529 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3409 | 2506 | -0.5618 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2534 | 1887 | -0.5542 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2314 | 1752 | -0.6638 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2162 | 1752 | -0.6638 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2162 | 1752 | -0.6638 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2197 | 1596 | -0.428 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2017 | 1531 | -0.6661 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1764 | 1362 | -0.6149 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1855 | 1359 | -0.398 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1987 | 1347 | -0.3373 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1987 | 1347 | -0.3373 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1673 | 1129 | -0.3123 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1229 | 912 | -0.5391 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 755 | 561 | -0.2661 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 784 | 469 | -0.4807 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 377 | 300 | -0.6838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 391 | 243 | -0.1477 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 763 | 203 | -0.2721 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 290 | 200 | -0.2712 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 290 | 200 | -0.2712 | `keep_collecting` |
| `would_limit_fill` | `false` | 824 | 199 | -0.2728 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 53, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 4183 | 3102 | -0.9508 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4183 | 3102 | -0.9508 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2423 | 2320 | -1.447 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2082 | 1553 | -1.028 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1894 | 1379 | -0.8439 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1165 | 1165 | -1.5045 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1009 | 1009 | -1.3798 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 256 | 235 | 0.2079 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 214 | 202 | 0.6224 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 207 | 170 | -1.1121 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 215 | 155 | 0.0277 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 146 | 146 | -1.452 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 131 | 124 | 2.0903 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 109 | 109 | 0.3037 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 98 | 98 | 0.7245 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 138 | 66 | -0.4617 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 64 | 64 | 2.2859 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 58 | 58 | 0.0026 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 53 | 53 | 1.9487 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 41 | 41 | -0.5404 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 275 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 72 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 197 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1081 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 275 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 515 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 529 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 84, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 4180 | 4180 | -1.3339 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2939 | 2939 | -1.0097 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2412 | 2412 | -0.9593 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2412 | 2412 | -0.9593 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2412 | 2412 | -0.9593 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1791 | 1791 | -1.1964 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1309 | 1309 | -1.2822 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1135 | 1135 | -1.5134 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1042 | 1042 | -0.516 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 895 | 895 | -1.8028 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 762 | 762 | -0.9344 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 630 | 630 | 0.5915 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 610 | 610 | -0.5121 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 531 | 531 | -0.5328 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 477 | 477 | -1.7162 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 436 | 436 | -1.1778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 395 | 395 | -0.8764 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 392 | 392 | -1.2526 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 355 | 355 | -2.4603 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 10348 | 275 | -0.1149 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 275 | 275 | -0.1149 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 275 | 275 | -0.1149 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 252 | 252 | 0.2485 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 226 | 226 | 0.064 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 219 | 219 | 0.7458 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 148 | 148 | -1.6829 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 139 | 139 | 2.4085 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 103 | 103 | -0.9539 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 92 | 92 | -0.3839 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 89 | 89 | 0.0988 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 78 | 78 | 1.2145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 71 | 71 | -0.2886 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 62 | 62 | 0.3252 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 57 | 57 | 0.7889 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 56 | 56 | 2.5073 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 50 | 50 | 0.9514 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 49 | 49 | 0.2598 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 1029, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 196939 | 196939 | None | -0.5014 | 0.2039 | `hold_sample` |
| `arm` | `AVG_DOWN` | 156558 | 155833 | None | -0.8011 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 111770 | 111770 | None | -0.5015 | 0.2026 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 109366 | 108641 | None | -0.9656 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 47192 | 47192 | None | -0.4223 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 42773 | 41149 | None | 0.6349 | 0.9768 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 42773 | 41149 | None | 0.6349 | 0.9768 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 36846 | 36846 | None | -0.4718 | 0.2138 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 34675 | 34675 | None | 0.5135 | 0.9808 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 25630 | 25630 | None | -0.5185 | 0.2055 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 19194 | 19194 | None | -0.3292 | 0.1584 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 12587 | 12587 | None | -0.5119 | 0.1911 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10106 | 10106 | None | -0.5506 | 0.1947 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4424 | 4424 | None | -0.4579 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2802 | 2802 | None | -0.8401 | 0.0889 | `hold_sample` |
| `blocker_reason` | `ok` | 1789 | 1789 | None | -2.4042 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1521 | 1521 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1513 | 1513 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1493 | 1493 | None | 3.3022 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1404 | 1404 | None | -1.1 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 550 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 275 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 550 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 275 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 550 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 275 | 275 | -0.1149 | -0.1532 | 0.3345 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 542 | 271 | -0.1141 | -0.1521 | 0.3395 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 394 | 197 | -0.0454 | -0.0606 | 0.3655 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 366 | 183 | -0.6512 | -0.8683 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 103 | 103 | -0.9539 | -1.2718 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 206 | 103 | -0.9539 | -1.2718 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 72 | 72 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 144 | 72 | -0.2744 | -0.3658 | 0.2778 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 144 | 72 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 60 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 120 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 104 | 52 | 0.274 | 0.3654 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 21 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 42 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 42 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |

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
