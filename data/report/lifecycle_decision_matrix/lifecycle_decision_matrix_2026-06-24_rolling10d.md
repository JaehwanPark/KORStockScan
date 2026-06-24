# Lifecycle Decision Matrix - 2026-06-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-24_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `108889`
- source_rows_total: `148694`
- retained_rows: `108889`
- dropped_rows_by_source: `{}`
- joined_rows: `93429`
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
- lifecycle_flow_bucket_count: `586`
- lifecycle_flow_complete_count: `622`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0063`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 8101 | 930 | 1.0372 | 0.9483 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1883 | 1125 | -0.3751 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1784 | 1125 | -0.9046 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 89557 | 88121 | -0.4551 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7564 | 2128 | -0.8745 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 586, 'complete_flow_count': 622, 'incomplete_flow_count': 97740, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 71354 | 70964 | -0.716 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 17179 | 16133 | 0.7099 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 825 | 825 | -0.9786 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 239 | 239 | 1.6552 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 206 | 206 | 1.8846 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 94 | 94 | 2.3735 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 76 | 76 | 0.0098 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 30 | 30 | -0.9613 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 23 | 23 | -0.6982 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 19 | 19 | -0.9734 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 16 | 16 | -2.1293 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 16 | 16 | -0.7994 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 11 | 11 | -1.4269 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 11 | 11 | -0.9164 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 11 | 11 | -1.1384 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 10 | 10 | -1.3089 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 9 | 9 | -0.5746 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 9 | 9 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.4858 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 8 | 8 | 0.7516 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 460, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5955 | 923 | 1.0372 | 1.1321 | 0.4789 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 5982 | 764 | 0.7586 | 0.4779 | 0.4502 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 546 | 546 | 1.8574 | 2.8273 | 0.6575 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 7717 | 546 | 1.8574 | 2.8273 | 0.6575 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 413 | 413 | 1.7482 | 2.6721 | 0.6392 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 1203 | 336 | 1.7694 | 2.6741 | 0.6547 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 6266 | 333 | -0.0969 | -1.2935 | 0.2312 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 822 | 322 | 1.4784 | 2.0713 | 0.5963 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 963 | 316 | 1.1921 | 1.7273 | 0.5728 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4234 | 300 | -0.1124 | -1.3425 | 0.21 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 4130 | 263 | 0.3432 | -0.4854 | 0.2966 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 3498 | 217 | -0.0321 | -1.1855 | 0.2304 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1586 | 197 | 1.3205 | 1.6145 | 0.5279 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 186 | 186 | -0.0461 | -1.9674 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1222 | 181 | 0.7269 | 0.5289 | 0.4199 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 376 | 172 | 1.6429 | 2.4468 | 0.5872 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 3927 | 164 | -0.0715 | -1.6892 | 0.1646 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 114 | 114 | 1.6122 | 2.4021 | 0.7369 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 744 | 103 | 1.3306 | 2.4107 | 0.602 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 102 | 102 | -0.1666 | -3.1002 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 99 | 99 | 1.4574 | 1.941 | 0.6262 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 81 | 81 | -0.2488 | 2.3581 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 416 | 72 | 0.5054 | -1.3847 | 0.2222 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 52 | 52 | 1.3233 | 1.6752 | 0.6346 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 746 | 50 | -0.2192 | -1.0152 | 0.26 | `hold_no_edge` |
| `score_band` | `score_lt60` | 1179 | 35 | -0.0489 | -0.6703 | 0.3429 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 648 | 32 | -0.2454 | -1.7731 | 0.125 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 679 | 30 | -0.1048 | -1.6057 | 0.1333 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 12 | 12 | 2.0293 | 3.4187 | 0.75 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 165, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1835 | 1125 | -0.3751 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1655 | 1125 | -0.3751 | `keep_collecting` |
| `latency_state` | `simulated` | 1655 | 1125 | -0.3751 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1826 | 1125 | -0.3751 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1645 | 1119 | -0.3689 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1563 | 1065 | -0.3813 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1502 | 1005 | -0.3672 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1374 | 913 | -0.396 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1287 | 867 | -0.3297 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1186 | 799 | -0.3182 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1086 | 733 | -0.3917 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 837 | 577 | -0.5667 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 766 | 577 | -0.5667 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 766 | 577 | -0.5667 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 886 | 545 | -0.1725 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 886 | 545 | -0.1725 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 789 | 482 | -0.151 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 361 | 285 | -0.657 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 370 | 262 | -0.5755 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 407 | 246 | -0.4033 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 310 | 227 | -0.6001 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 362 | 218 | -0.0532 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 279 | 206 | -0.2487 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 305 | 120 | -0.4411 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 137 | 82 | -0.2519 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 234 | 63 | -0.2688 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 320 | 60 | -0.2655 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 92 | 60 | -0.2655 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 92 | 60 | -0.2655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 54 | 43 | -0.4438 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 51 | 38 | -0.1476 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1654 | 1125 | -0.9046 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1654 | 1125 | -0.9046 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 896 | 853 | -1.4072 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1196 | 798 | -0.8959 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 608 | 608 | -1.4011 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 405 | 283 | -0.8967 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 207 | 207 | -1.4154 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 81 | 75 | 0.7972 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 79 | 71 | 0.3105 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 53 | 53 | 0.3203 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 53 | 53 | 0.7845 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 52 | 49 | 2.3024 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 53 | 44 | -1.1119 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 75 | 42 | 0.0224 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 38 | 38 | -1.4595 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 72 | 35 | -0.3689 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 34 | 34 | 2.6767 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 25 | 25 | -0.106 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.4 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.8336 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | 0.1888 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | 0.242 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 1.3648 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.291 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 130 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 20 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 105 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 529 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 130 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 398 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 122 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 69, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1557 | 1557 | -1.2904 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1009 | 1009 | -0.871 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1009 | 1009 | -0.871 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1009 | 1009 | -0.871 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 989 | 989 | -0.9883 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 714 | 714 | -1.1606 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 456 | 456 | -1.1805 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 378 | 378 | -1.5084 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 337 | 337 | -0.4362 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 334 | 334 | -1.8012 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 274 | 274 | -0.9498 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 274 | 274 | -0.489 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 238 | 238 | -0.5216 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 181 | 181 | 0.9138 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 172 | 172 | -1.0693 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 157 | 157 | -1.6345 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 142 | 142 | -1.1902 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 5566 | 130 | -0.0353 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 130 | 130 | -0.0353 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 130 | 130 | -0.0353 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 130 | 130 | -2.5556 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 127 | 127 | -0.7699 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 86 | 86 | 0.9346 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 82 | 82 | 0.4235 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 70 | 70 | 0.1108 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 62 | 62 | -1.6185 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 59 | 59 | 2.7035 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 43 | 43 | -0.8651 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 36 | 36 | -0.2738 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 36 | 36 | 0.2511 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 34 | 34 | 0.1895 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 30 | 30 | -0.1332 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 28 | 28 | 0.2668 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 27 | 27 | 1.5495 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 22 | 22 | 2.9264 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 20 | 20 | 0.8052 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 16 | 16 | 0.4282 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 14 | 14 | 1.0043 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 14 | 14 | 0.7954 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 649, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 88090 | 88090 | None | -0.5107 | 0.1787 | `hold_sample` |
| `arm` | `AVG_DOWN` | 72280 | 71890 | None | -0.7743 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 56793 | 56793 | None | -0.5044 | 0.1822 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 49767 | 49377 | None | -0.9345 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 22513 | 22513 | None | -0.4231 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 17277 | 16231 | None | 0.6598 | 0.9711 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 17277 | 16231 | None | 0.6598 | 0.9711 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 15012 | 15012 | None | -0.5246 | 0.1665 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 12795 | 12795 | None | 0.4831 | 0.978 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 11191 | 11191 | None | -0.3465 | 0.1308 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 7713 | 7713 | None | -0.5272 | 0.1736 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 4515 | 4515 | None | -0.4923 | 0.1794 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4057 | 4057 | None | -0.5365 | 0.1834 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1866 | 1866 | None | -0.4658 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1192 | 1192 | None | -0.7915 | 0.099 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 987 | 987 | None | 3.1543 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 678 | 678 | None | -2.446 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 674 | 674 | None | -0.3586 | 0.3531 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 591 | 591 | None | -0.93 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 575 | 575 | None | -0.75 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 260 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 130 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 260 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 130 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 260 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 130 | 130 | -0.0353 | -0.0471 | 0.3461 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 252 | 126 | -0.031 | -0.0413 | 0.3571 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 210 | 105 | 0.0537 | 0.0715 | 0.3905 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 170 | 85 | -0.557 | -0.7427 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 43 | 43 | -0.8651 | -1.1535 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 86 | 43 | -0.8651 | -1.1535 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 37 | 37 | -0.2684 | -0.3578 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 74 | 37 | -0.2684 | -0.3578 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 33 | 33 | 0.1975 | 0.2633 | 0.8485 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 66 | 33 | 0.1975 | 0.2633 | 0.8485 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 56 | 28 | 0.2406 | 0.3207 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 40 | 20 | -0.378 | -0.504 | 0.2 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 8 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 16 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |

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
