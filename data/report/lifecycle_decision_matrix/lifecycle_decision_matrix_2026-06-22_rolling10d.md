# Lifecycle Decision Matrix - 2026-06-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-22_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `94897`
- source_rows_total: `130975`
- retained_rows: `94897`
- dropped_rows_by_source: `{}`
- joined_rows: `84753`
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
- lifecycle_flow_bucket_count: `519`
- lifecycle_flow_complete_count: `534`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0062`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 6801 | 753 | 1.099 | 0.9567 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1524 | 912 | -0.2963 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1435 | 912 | -0.8153 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 81825 | 80524 | -0.4529 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3312 | 1652 | -0.8316 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 519, 'complete_flow_count': 534, 'incomplete_flow_count': 85680, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 65494 | 65149 | -0.7102 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 15547 | 14591 | 0.7093 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 621 | 621 | -0.9739 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 193 | 193 | 1.7913 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 165 | 165 | 1.8407 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 81 | 81 | 2.2752 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 52 | 52 | 0.0815 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 28 | 28 | -0.9596 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 21 | 21 | -0.6628 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 14 | 14 | -0.7857 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 13 | 13 | -2.1853 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 11 | 11 | -0.9164 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 10 | 10 | -1.3089 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 10 | 10 | -1.258 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 9 | 9 | -1.4135 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.4858 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 8 | 8 | 0.7516 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 8 | 8 | -0.2747 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 7 | 7 | -2.5363 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 423, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5061 | 746 | 1.0996 | 1.1978 | 0.5 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 5193 | 631 | 0.7828 | 0.5108 | 0.4691 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 446 | 446 | 1.8856 | 2.8387 | 0.6794 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 6494 | 446 | 1.8856 | 2.8387 | 0.6794 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 999 | 313 | 1.7534 | 2.6387 | 0.6645 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 313 | 313 | 1.7534 | 2.6387 | 0.6645 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 724 | 293 | 1.5289 | 2.1755 | 0.6178 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 5386 | 264 | 0.0077 | -1.2387 | 0.2424 | `hold_no_edge` |
| `score_band` | `score_70p` | 781 | 258 | 1.3157 | 1.9281 | 0.6008 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 3829 | 227 | 0.4063 | -0.3929 | 0.3128 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3524 | 223 | 0.0109 | -1.2398 | 0.2242 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 3355 | 196 | 0.0019 | -1.0841 | 0.2449 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1402 | 174 | 1.4232 | 1.7888 | 0.5632 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 147 | 147 | 0.0229 | -1.9635 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 944 | 141 | 0.8281 | 0.7529 | 0.4539 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 293 | 129 | 1.5248 | 2.1995 | 0.6046 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 3225 | 119 | 0.0607 | -1.5972 | 0.1849 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 103 | 103 | 1.6775 | 2.5033 | 0.7476 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 92 | 92 | 1.5724 | 2.1166 | 0.6522 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 78 | 78 | -0.0222 | -3.031 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 72 | 72 | -0.2612 | 2.3789 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 359 | 63 | 0.5183 | -1.3041 | 0.2381 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 51 | 51 | 1.3817 | 1.7475 | 0.6471 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 707 | 42 | -0.1154 | -0.8119 | 0.3095 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 675 | 30 | -0.1048 | -1.6057 | 0.1333 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 559 | 27 | 0.0461 | -1.5559 | 0.1482 | `hold_no_edge` |
| `score_band` | `score_lt60` | 975 | 26 | -0.0155 | -0.7411 | 0.3077 | `hold_no_edge` |

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
| `actual_order_submitted` | `false` | 1486 | 912 | -0.2963 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1319 | 912 | -0.2963 | `keep_collecting` |
| `latency_state` | `simulated` | 1319 | 912 | -0.2963 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1477 | 912 | -0.2963 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1312 | 906 | -0.2881 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1227 | 852 | -0.2984 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1169 | 796 | -0.2756 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1089 | 736 | -0.298 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 979 | 671 | -0.2016 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 893 | 612 | -0.1847 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 832 | 570 | -0.2877 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 662 | 459 | -0.4903 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 597 | 459 | -0.4903 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 597 | 459 | -0.4903 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 720 | 451 | -0.099 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 720 | 451 | -0.099 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 625 | 388 | -0.0603 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 328 | 236 | -0.594 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 374 | 230 | -0.4178 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 285 | 212 | -0.6232 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 245 | 201 | -0.478 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 228 | 170 | -0.2452 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 243 | 152 | 0.0614 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 279 | 116 | -0.4384 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 226 | 62 | -0.2656 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 297 | 60 | -0.2655 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 92 | 60 | -0.2655 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 92 | 60 | -0.2655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 79 | 50 | 0.1264 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 44 | 36 | -0.3335 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 35 | -0.2227 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1318 | 912 | -0.8153 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1318 | 912 | -0.8153 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 716 | 679 | -1.3472 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 905 | 611 | -0.7896 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 456 | 456 | -1.3343 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 365 | 260 | -0.8469 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 188 | 188 | -1.3771 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 71 | 63 | 0.3625 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 68 | 62 | 0.9031 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 45 | 45 | 0.3948 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 48 | 41 | -0.9976 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 44 | 41 | 2.356 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 41 | 41 | 0.9882 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 67 | 36 | 0.1847 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 35 | 35 | -1.3554 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 63 | 31 | -0.3516 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 27 | 27 | 2.7202 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 23 | 23 | -0.3843 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 20 | 20 | 0.7385 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 19 | 19 | 0.1609 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | 0.1888 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | 0.242 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 1.5903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.2575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 117 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 17 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 100 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 406 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 117 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 294 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 105 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 28 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1190 | 1190 | -1.2616 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 773 | 773 | -0.9297 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 762 | 762 | -0.8627 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 762 | 762 | -0.8627 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 762 | 762 | -0.8627 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 530 | 530 | -1.1609 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 359 | 359 | -1.1386 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 281 | 281 | -1.3749 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 258 | 258 | -0.4638 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 254 | 254 | -1.7413 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 234 | 234 | -0.9088 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 225 | 225 | -0.4885 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 194 | 194 | -0.5244 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 154 | 154 | -1.0728 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 149 | 149 | 0.9009 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 1777 | 117 | 0.0192 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 117 | 117 | 0.0192 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 117 | 117 | 0.0192 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 107 | 107 | -1.1262 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 106 | 106 | -1.5303 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 101 | 101 | -2.482 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 99 | 99 | -0.8217 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 71 | 71 | 0.4565 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 67 | 67 | 0.938 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 51 | 51 | 0.2017 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 48 | 48 | 2.7464 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 46 | 46 | -1.5459 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 37 | 37 | -0.8513 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 32 | 32 | 0.1842 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 31 | 31 | -0.2637 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 31 | 31 | 0.4137 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 24 | 24 | -0.0791 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 18 | 18 | 1.3801 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 17 | 17 | 0.9572 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 16 | 16 | 2.7793 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 15 | 15 | 0.274 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 15 | 15 | 0.4161 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 13 | 13 | 0.8028 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 11 | 11 | 0.9964 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 502, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 80496 | 80496 | None | -0.5088 | 0.1771 | `hold_sample` |
| `arm` | `AVG_DOWN` | 66204 | 65859 | None | -0.768 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 53322 | 53322 | None | -0.5086 | 0.1777 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 45455 | 45110 | None | -0.925 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 20749 | 20749 | None | -0.4264 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 15621 | 14665 | None | 0.6577 | 0.9739 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 15621 | 14665 | None | 0.6577 | 0.9739 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 13315 | 13315 | None | -0.5184 | 0.1674 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 11510 | 11510 | None | 0.4842 | 0.9804 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 10662 | 10662 | None | -0.3448 | 0.1329 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 6449 | 6449 | None | -0.5106 | 0.1773 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3932 | 3932 | None | -0.4729 | 0.1872 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3478 | 3478 | None | -0.5118 | 0.1949 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1654 | 1654 | None | -0.4687 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 915 | 915 | None | -0.7496 | 0.0973 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 894 | 894 | None | 3.157 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 601 | 601 | None | -0.36 | 0.3561 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 574 | 574 | None | -0.2964 | 0.1376 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 558 | 558 | None | -0.92 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 539 | 539 | None | -2.3878 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 234 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 117 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 234 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 117 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 234 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 117 | 117 | 0.0192 | 0.0256 | 0.3675 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 230 | 115 | 0.0225 | 0.03 | 0.3739 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 200 | 100 | 0.0802 | 0.1069 | 0.4 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 148 | 74 | -0.5401 | -0.7201 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 37 | 37 | -0.8513 | -1.1351 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 74 | 37 | -0.8513 | -1.1351 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 32 | 32 | -0.2578 | -0.3437 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 64 | 32 | -0.2578 | -0.3437 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 31 | 31 | 0.1926 | 0.2568 | 0.8387 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 62 | 31 | 0.1926 | 0.2568 | 0.8387 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 52 | 26 | 0.238 | 0.3173 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 34 | 17 | -0.3397 | -0.453 | 0.1765 | `hold_sample` |
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
