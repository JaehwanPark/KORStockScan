# Lifecycle Decision Matrix - 2026-06-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-10_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `87322`
- source_rows_total: `148235`
- retained_rows: `87322`
- dropped_rows_by_source: `{}`
- joined_rows: `82549`
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
- lifecycle_flow_bucket_count: `396`
- lifecycle_flow_complete_count: `377`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0047`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3455 | 652 | 0.6674 | 0.994 | `pass` | `NO_CHANGE` | False |
| `submit` | 1462 | 1270 | -0.4349 | 0.9955 | `pass` | `NO_CHANGE` | False |
| `holding` | 1368 | 1270 | -0.9479 | 0.995 | `pass` | `EXIT` | False |
| `scale_in` | 77267 | 76918 | -0.4259 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3770 | 2439 | -0.9803 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 396, 'complete_flow_count': 377, 'incomplete_flow_count': 80433, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 58475 | 58347 | -0.7479 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 17799 | 17578 | 0.6685 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 845 | 845 | -1.1172 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 157 | 157 | 1.2426 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 112 | 112 | 1.1556 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 98 | 98 | 1.6304 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 64 | 64 | -0.5437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 22 | 22 | -0.9309 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 15 | 15 | -0.8507 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 14 | 14 | -0.8307 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 7 | 7 | -1.0471 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 6 | 6 | -1.9202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 6 | 6 | -1.771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 5 | 5 | -0.9619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:23320ac43e` | 5 | 5 | -0.1805 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 334, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1920 | 650 | 0.6718 | 0.7408 | 0.4615 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1709 | 453 | 0.4884 | 0.0927 | 0.4304 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 367 | 367 | 1.3196 | 2.259 | 0.6294 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3170 | 367 | 1.3196 | 2.259 | 0.6294 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1945 | 265 | -0.1556 | -1.2914 | 0.2226 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1049 | 253 | 0.7425 | 1.3767 | 0.5889 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 253 | 253 | 0.7425 | 1.3767 | 0.5889 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 777 | 222 | 0.0984 | -0.8104 | 0.2928 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 285 | 206 | 0.7331 | 1.2667 | 0.568 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 649 | 198 | -0.0729 | -1.387 | 0.2121 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 794 | 197 | -0.0712 | -1.3994 | 0.2081 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 666 | 196 | 0.2728 | 0.1936 | 0.4796 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 147 | 147 | -0.1728 | -1.9544 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 1031 | 127 | -0.066 | -1.3241 | 0.2047 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 582 | 123 | 0.3278 | 0.0949 | 0.374 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 208 | 107 | 0.7796 | 1.1084 | 0.5047 | `source_quality_workorder` |
| `score_band` | `score_70p` | 207 | 102 | 0.2605 | 0.673 | 0.5294 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 390 | 92 | 0.7851 | 0.8941 | 0.4348 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 444 | 92 | 0.8043 | 0.5327 | 0.4021 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 225 | 87 | 1.345 | 3.2021 | 0.6207 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 67 | 67 | -0.1777 | 1.6609 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 53 | 53 | 0.6575 | 0.8313 | 0.6038 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 78, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1744 | 1721 | -0.3607 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1730 | 1353 | -0.4134 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1285 | 1270 | -0.4349 | `keep_collecting` |
| `latency_state` | `simulated` | 1285 | 1270 | -0.4349 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1454 | 1270 | -0.4349 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1202 | 1187 | -0.4593 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1047 | 1032 | -0.4253 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1045 | 1017 | -0.4667 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 825 | 821 | -0.4816 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 826 | 819 | -0.5906 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 862 | 805 | -0.5786 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 812 | 805 | -0.5786 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 739 | 735 | -0.4196 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 698 | 684 | -0.4039 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 501 | 500 | -0.5374 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 481 | 470 | -0.4309 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 473 | 465 | -0.186 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 431 | 424 | -0.5584 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 385 | 377 | -0.178 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 371 | 360 | -0.4173 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 247 | 240 | -0.0998 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 239 | 239 | -0.2499 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 238 | 238 | -0.4764 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 188 | 188 | -0.5135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 126 | 125 | -0.3437 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 122 | 122 | -0.285 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 83 | 83 | -0.0852 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 260 | 83 | -0.0852 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 83 | 83 | -0.0852 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 76 | 76 | -0.0297 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 64 | 64 | -0.6458 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 30 | 30 | -2.3126 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 19 | 19 | -0.7139 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 14 | 14 | -1.2802 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -0.7024 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | 0.0012 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 7 | 7 | -0.6878 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 6 | 6 | 0.0698 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -2.459 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.678 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1285 | 1270 | -0.9479 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1285 | 1270 | -0.9479 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1006 | 975 | -1.3938 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 808 | 805 | -0.9922 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 621 | 621 | -1.4569 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 379 | 375 | -0.8407 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 276 | 276 | -1.2781 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 107 | 98 | 0.2784 | `hold_sample` |
| `holding_action` | `BUY` | 98 | 90 | -0.9991 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 78 | 78 | -1.3006 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 91 | 75 | 0.1297 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 72 | 68 | 0.6036 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 62 | 62 | 0.1886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 49 | 49 | 0.1521 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 44 | 44 | 0.5994 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 44 | 41 | 1.9749 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 35 | 35 | 0.3916 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 26 | 26 | 0.0875 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 25 | 25 | 2.4538 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 17 | 17 | 0.5222 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 33 | 13 | -0.3045 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 1.3147 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.3452 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.8275 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 0.9627 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 83 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 32 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 51 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 83 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 20 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 9 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 69, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1864 | 1864 | -1.3234 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1380 | 1380 | -0.9695 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 976 | 976 | -1.0633 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 976 | 976 | -1.0633 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 976 | 976 | -1.0633 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 767 | 767 | -1.2326 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 614 | 614 | -1.2459 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 529 | 529 | -1.5121 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 506 | 506 | -0.4765 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 396 | 396 | -1.7538 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 345 | 345 | -0.8609 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 307 | 307 | 0.4858 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 222 | 222 | -1.6639 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 217 | 217 | -0.5189 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 205 | 205 | -0.852 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 193 | 193 | -0.5479 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 187 | 187 | -1.1815 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 169 | 169 | -1.1748 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 166 | 166 | -0.1836 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 166 | 166 | -2.3769 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 123 | 123 | 0.2498 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 108 | 108 | 0.0976 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 1414 | 83 | -0.1836 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 80 | 80 | 0.6413 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 61 | 61 | -1.6622 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 59 | 59 | -0.4457 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 49 | 49 | -0.3749 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 47 | 47 | 2.0366 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 33 | 33 | 1.0042 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 31 | 31 | -1.1412 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 31 | 31 | 0.895 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 30 | 30 | 0.4131 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 29 | 29 | 0.5056 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 28 | 28 | -0.4118 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 27 | 27 | -0.0926 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 24 | 24 | -0.4708 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 23 | 23 | 2.4331 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 23 | 23 | 0.023 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 20 | 20 | -0.3072 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -0.8469 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 469, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 102467 | 102211 | -0.8141 | -0.8963 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 76913 | 76913 | -0.426 | -0.5051 | 0.2252 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 40362 | 40362 | -0.4336 | -0.5169 | 0.2216 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 35734 | 35292 | 0.6675 | 0.5925 | 0.9817 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 16333 | 16333 | -0.3595 | -0.4281 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 15313 | 15313 | 0.6299 | 0.5488 | 0.9845 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 15294 | 15294 | -0.3637 | -0.4444 | 0.2482 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 11286 | 11286 | -0.472 | -0.5348 | 0.2274 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 7341 | 7341 | -0.2783 | -0.2984 | 0.2046 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 5489 | 5489 | -0.4366 | -0.512 | 0.1996 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 4482 | 4482 | -0.4419 | -0.5226 | 0.2044 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1649 | 1649 | -0.4312 | -0.457 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1131 | 1131 | -0.924 | -0.9238 | 0.0698 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 925 | 925 | -0.8593 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 898 | 898 | -1.0556 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 800 | 800 | -0.7181 | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 751 | 751 | -1.2546 | -1.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 746 | 746 | -1.9164 | -2.3543 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 723 | 723 | -0.6647 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 716 | 716 | -0.9233 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 669 | 669 | -1.0115 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 628 | 628 | -1.2667 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 593 | 593 | -0.2755 | -0.3119 | 0.2378 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 581 | 581 | -0.8645 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 505 | 505 | -1.0925 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 499 | 499 | -0.8063 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 489 | 489 | -0.6517 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 487 | 487 | -0.7856 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 480 | 480 | -0.9418 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 470 | 470 | -0.9671 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 438 | 438 | -0.6816 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 433 | 433 | -0.9334 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 415 | 415 | -0.8538 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 399 | 399 | -0.7336 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 398 | 398 | -1.0551 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 390 | 390 | -0.9711 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 368 | 368 | -0.7153 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 368 | 368 | -0.8756 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 366 | 366 | -0.7561 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 365 | 365 | -0.8498 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 249 | 166 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 166 | 83 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 83 | 83 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 166 | 83 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 166 | 83 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 83 | 83 | -0.1836 | -0.2448 | 0.3614 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 106 | 53 | -0.7854 | -1.0472 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 102 | 51 | -0.1681 | -0.2241 | 0.3921 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 64 | 32 | -0.2083 | -0.2778 | 0.3125 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 31 | 31 | -1.1412 | -1.5216 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 62 | 31 | -1.1412 | -1.5216 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 20 | 20 | -0.3072 | -0.4095 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 40 | 20 | -0.3072 | -0.4095 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 16 | 16 | 0.2681 | 0.3575 | 0.875 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 32 | 16 | 0.2681 | 0.3575 | 0.875 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 28 | 14 | 0.3139 | 0.4186 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 9 | 9 | 0.805 | 1.0733 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 18 | 9 | 0.805 | 1.0733 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 18 | 9 | 0.805 | 1.0733 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 4 | 4 | 1.5094 | 2.0125 | 1.0 | `hold_sample` |

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
