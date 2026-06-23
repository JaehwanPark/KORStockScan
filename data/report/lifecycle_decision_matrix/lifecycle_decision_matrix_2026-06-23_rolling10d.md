# Lifecycle Decision Matrix - 2026-06-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-23_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `102697`
- source_rows_total: `140607`
- retained_rows: `102697`
- dropped_rows_by_source: `{}`
- joined_rows: `89506`
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
- lifecycle_flow_bucket_count: `565`
- lifecycle_flow_complete_count: `590`
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
| `entry` | 7430 | 823 | 1.0297 | 0.9415 | `pass` | `NO_CHANGE` | False |
| `submit` | 1747 | 1056 | -0.3585 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1656 | 1056 | -0.8862 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 85957 | 84605 | -0.4543 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5907 | 1966 | -0.8682 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 565, 'complete_flow_count': 590, 'incomplete_flow_count': 92385, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 68610 | 68245 | -0.7141 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 16410 | 15423 | 0.7113 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 745 | 745 | -0.9834 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 211 | 211 | 1.8036 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 168 | 168 | 1.7954 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 83 | 83 | 2.3764 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 73 | 73 | 0.0435 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 30 | 30 | -0.9613 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 23 | 23 | -0.6982 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 16 | 16 | -0.7994 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 16 | 16 | -1.2862 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 15 | 15 | -2.143 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 11 | 11 | -1.4269 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 11 | 11 | -0.9164 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 11 | 11 | -1.1384 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 10 | 10 | -1.3089 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 9 | 9 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 8 | 8 | -0.4428 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.4858 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 8 | 8 | 0.7516 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 439, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5437 | 816 | 1.0296 | 1.0648 | 0.4792 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 5536 | 681 | 0.7612 | 0.4203 | 0.4508 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 469 | 469 | 1.8905 | 2.8542 | 0.6716 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 7076 | 469 | 1.8905 | 2.8542 | 0.6716 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 1203 | 336 | 1.7694 | 2.6741 | 0.6547 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 336 | 336 | 1.7694 | 2.6741 | 0.6547 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 822 | 322 | 1.4784 | 2.0713 | 0.5963 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 5791 | 304 | -0.0713 | -1.3297 | 0.2303 | `hold_no_edge` |
| `score_band` | `score_70p` | 877 | 285 | 1.2614 | 1.853 | 0.5824 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3836 | 270 | -0.0867 | -1.3843 | 0.2074 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 4130 | 263 | 0.3432 | -0.4854 | 0.2966 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 3498 | 217 | -0.0321 | -1.1855 | 0.2304 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1586 | 197 | 1.3205 | 1.6145 | 0.5279 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1222 | 181 | 0.7269 | 0.5289 | 0.4199 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 172 | 172 | -0.0332 | -1.9721 | 0.0 | `hold_no_edge` |
| `score_band` | `score_60_62` | 3568 | 145 | -0.0129 | -1.7256 | 0.1655 | `hold_no_edge` |
| `score_band` | `score_66_69` | 300 | 133 | 1.4672 | 2.086 | 0.5864 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 106 | 106 | 1.6744 | 2.5143 | 0.7453 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 94 | 94 | -0.1241 | -3.1097 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 93 | 93 | 1.5497 | 2.083 | 0.6451 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 77 | 77 | -0.3224 | 2.323 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 389 | 68 | 0.4536 | -1.3941 | 0.2206 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 51 | 51 | 1.3817 | 1.7475 | 0.6471 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 718 | 45 | -0.0188 | -0.8958 | 0.2889 | `hold_no_edge` |
| `score_band` | `score_lt60` | 1109 | 34 | -0.0816 | -0.7529 | 0.3235 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 648 | 32 | -0.2454 | -1.7731 | 0.125 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 675 | 30 | -0.1048 | -1.6057 | 0.1333 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 154, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1707 | 1056 | -0.3585 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1531 | 1056 | -0.3585 | `keep_collecting` |
| `latency_state` | `simulated` | 1531 | 1056 | -0.3585 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1698 | 1056 | -0.3585 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1523 | 1050 | -0.3518 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1439 | 996 | -0.3641 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1378 | 937 | -0.3455 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1261 | 854 | -0.3785 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1167 | 800 | -0.3015 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1068 | 732 | -0.2863 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 995 | 681 | -0.3595 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 781 | 545 | -0.5493 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 713 | 545 | -0.5493 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 713 | 545 | -0.5493 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 815 | 508 | -0.154 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 815 | 508 | -0.154 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 719 | 445 | -0.128 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 322 | 262 | -0.5968 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 364 | 260 | -0.5848 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 386 | 235 | -0.4292 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 306 | 225 | -0.611 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 267 | 196 | -0.2356 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 315 | 193 | -0.0383 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 293 | 119 | -0.4611 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 120 | 77 | -0.2072 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 233 | 63 | -0.2688 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 308 | 60 | -0.2655 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 92 | 60 | -0.2655 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 92 | 60 | -0.2655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 46 | 38 | -0.4361 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 49 | 38 | -0.1476 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1530 | 1056 | -0.8862 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1530 | 1056 | -0.8862 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 837 | 797 | -1.3953 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1081 | 733 | -0.8735 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 556 | 556 | -1.3862 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 399 | 281 | -0.8924 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 205 | 205 | -1.4146 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 77 | 71 | 0.8244 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 78 | 70 | 0.3063 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 52 | 52 | 0.3148 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 49 | 49 | 0.823 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 48 | 45 | 2.2725 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 50 | 42 | -1.0664 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 72 | 39 | 0.1637 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 36 | 36 | -1.4257 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 70 | 34 | -0.3653 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 30 | 30 | 2.6818 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 24 | 24 | -0.3962 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 22 | 22 | 0.1269 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.8336 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | 0.1888 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | 0.242 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 1.3648 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.291 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 126 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 20 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 105 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 474 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 126 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 348 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 118 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 33 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1430 | 1430 | -1.2893 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 921 | 921 | -0.982 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 919 | 919 | -0.8708 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 919 | 919 | -0.8708 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 919 | 919 | -0.8708 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 644 | 644 | -1.1662 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 425 | 425 | -1.1722 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 351 | 351 | -1.4698 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 311 | 311 | -1.7878 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 310 | 310 | -0.4464 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 260 | 260 | -0.9621 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 258 | 258 | -0.4847 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 223 | 223 | -0.5183 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 173 | 173 | 0.8742 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 168 | 168 | -1.0737 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 140 | 140 | -1.6175 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 130 | 130 | -1.1797 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 4067 | 126 | -0.0167 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 126 | 126 | -0.0167 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 126 | 126 | -0.0167 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 123 | 123 | -2.514 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 117 | 117 | -0.7807 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 80 | 80 | 0.4158 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 79 | 79 | 0.9038 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 65 | 65 | 0.1922 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 58 | 58 | -1.6107 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 54 | 54 | 2.6824 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 40 | 40 | -0.8769 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 35 | 35 | -0.2711 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 35 | 35 | 0.2712 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 34 | 34 | 0.1895 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 30 | 30 | -0.1332 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 26 | 26 | 0.26 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 24 | 24 | 1.4393 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 20 | 20 | 2.9093 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 19 | 19 | 0.8196 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 15 | 15 | 0.4161 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 14 | 14 | 0.7954 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 13 | 13 | 1.0161 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 569, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 84575 | 84575 | None | -0.5107 | 0.1787 | `hold_sample` |
| `arm` | `AVG_DOWN` | 69452 | 69087 | None | -0.773 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 55173 | 55173 | None | -0.5093 | 0.1808 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 47813 | 47448 | None | -0.9322 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 21639 | 21639 | None | -0.424 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 16505 | 15518 | None | 0.6594 | 0.9753 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 16505 | 15518 | None | 0.6594 | 0.9753 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 14085 | 14085 | None | -0.5197 | 0.1678 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 12217 | 12217 | None | 0.4873 | 0.9816 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 10919 | 10919 | None | -0.3463 | 0.1329 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 7172 | 7172 | None | -0.5167 | 0.1772 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 4297 | 4297 | None | -0.4743 | 0.1841 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3848 | 3848 | None | -0.5275 | 0.1845 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1758 | 1758 | None | -0.4654 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1099 | 1099 | None | -0.7798 | 0.1047 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 926 | 926 | None | 3.171 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 635 | 635 | None | -2.4301 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 635 | 635 | None | -0.3648 | 0.3575 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 587 | 587 | None | -0.93 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 574 | 574 | None | -0.2964 | 0.1376 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 252 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 126 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 252 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 126 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 252 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 126 | 126 | -0.0167 | -0.0222 | 0.3571 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 244 | 122 | -0.0116 | -0.0154 | 0.3688 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 210 | 105 | 0.0537 | 0.0715 | 0.3905 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 162 | 81 | -0.5538 | -0.7384 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 40 | 40 | -0.8769 | -1.1693 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 80 | 40 | -0.8769 | -1.1693 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 36 | 36 | -0.2656 | -0.3542 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 72 | 36 | -0.2656 | -0.3542 | 0.0 | `candidate_tighten_or_exclude` |
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
