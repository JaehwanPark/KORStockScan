# Lifecycle Decision Matrix - 2026-06-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-19_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `212926`
- source_rows_total: `317868`
- retained_rows: `212926`
- dropped_rows_by_source: `{}`
- joined_rows: `194664`
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
- lifecycle_flow_bucket_count: `854`
- lifecycle_flow_complete_count: `1048`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0054`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 11260 | 1579 | 0.7214 | 0.9706 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4061 | 2710 | -0.5129 | 0.9979 | `pass` | `NO_CHANGE` | False |
| `holding` | 3810 | 2710 | -0.92 | 0.9976 | `pass` | `EXIT` | False |
| `scale_in` | 184829 | 182845 | -0.4324 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 8966 | 4820 | -0.9432 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 854, 'complete_flow_count': 1048, 'incomplete_flow_count': 193434, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 143367 | 142747 | -0.7243 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 39414 | 38050 | 0.6822 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1699 | 1699 | -1.0565 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 347 | 347 | 1.5695 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 289 | 289 | 1.6759 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 203 | 203 | 1.5274 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 140 | 140 | -0.2926 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 61 | 61 | -0.9074 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 39 | 39 | -0.8039 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 32 | 32 | -0.9106 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 20 | 20 | -2.0219 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 15 | 15 | -0.5468 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 14 | 14 | -0.9141 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 13 | 13 | -0.7433 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 13 | 13 | -1.2754 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 12 | 12 | -1.0708 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 12 | 12 | -0.2913 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 491, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 7625 | 1572 | 0.7194 | 0.8072 | 0.4695 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 7403 | 1183 | 0.5805 | 0.274 | 0.4488 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 844 | 844 | 1.598 | 2.558 | 0.66 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 10525 | 844 | 1.598 | 2.558 | 0.66 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 8015 | 677 | -0.2704 | -1.2407 | 0.2422 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2354 | 597 | 1.2732 | 2.0738 | 0.6365 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 597 | 597 | 1.2732 | 2.0738 | 0.6365 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 5174 | 575 | -0.0046 | -0.7362 | 0.3009 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4749 | 564 | -0.2821 | -1.2719 | 0.2358 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5087 | 551 | -0.2925 | -1.2604 | 0.2377 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1115 | 536 | 1.1275 | 1.7468 | 0.5952 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2423 | 452 | 0.6301 | 0.7149 | 0.4978 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 964 | 352 | 1.0006 | 1.6328 | 0.5909 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 350 | 350 | -0.2068 | -1.9753 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 4781 | 345 | -0.2872 | -1.3279 | 0.2203 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1641 | 274 | 0.5983 | 0.4741 | 0.427 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 444 | 231 | 1.2432 | 1.8224 | 0.6017 | `hold_sample` |
| `score_band` | `score_63_65` | 779 | 194 | 0.6551 | 0.9352 | 0.4948 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 974 | 181 | 1.1567 | 1.5302 | 0.5138 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 1519 | 181 | -0.0058 | -0.3004 | 0.337 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 179 | 179 | -0.549 | 1.9621 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 109 | 109 | 1.0404 | 1.3738 | 0.633 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 172, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3928 | 2710 | -0.5129 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3572 | 2710 | -0.5129 | `keep_collecting` |
| `latency_state` | `simulated` | 3572 | 2710 | -0.5129 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3911 | 2710 | -0.5129 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3529 | 2678 | -0.498 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3286 | 2513 | -0.5329 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2956 | 2250 | -0.5203 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2898 | 2194 | -0.5506 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2081 | 1589 | -0.5476 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2005 | 1542 | -0.663 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1869 | 1542 | -0.663 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1869 | 1542 | -0.663 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1930 | 1469 | -0.6793 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1707 | 1323 | -0.6261 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1651 | 1250 | -0.3713 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1671 | 1168 | -0.3146 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1671 | 1168 | -0.3146 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1337 | 1033 | -0.3268 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1365 | 955 | -0.2866 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1166 | 883 | -0.5473 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 656 | 484 | -0.2595 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 730 | 460 | -0.4765 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 286 | 197 | -0.2568 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 741 | 197 | -0.2568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 286 | 197 | -0.2568 | `keep_collecting` |
| `would_limit_fill` | `false` | 774 | 196 | -0.2584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 191 | 165 | -0.5202 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 211 | 135 | -0.7204 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 3572 | 2710 | -0.92 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3572 | 2710 | -0.92 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2102 | 2010 | -1.4276 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1996 | 1494 | -1.0226 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1115 | 1115 | -1.5025 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1379 | 1054 | -0.7521 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 757 | 757 | -1.3192 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 235 | 218 | 0.2215 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 186 | 177 | 0.6055 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 197 | 162 | -1.0662 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 197 | 143 | 0.0634 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 138 | 138 | -1.4179 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 115 | 109 | 2.1196 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 94 | 94 | 0.0189 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 92 | 92 | 0.3536 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 91 | 91 | 0.4683 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 75 | 75 | 0.7457 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 113 | 53 | -0.3632 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 53 | 53 | 2.3362 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 49 | 49 | 1.9917 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 47 | 47 | 0.1161 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 30 | 30 | -0.3929 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 23 | 23 | -0.3244 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 238 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 67 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 171 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 862 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 238 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 325 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 502 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 65 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 39 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3585 | 3585 | -1.3284 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2562 | 2562 | -0.9855 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2020 | 2020 | -0.9849 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2020 | 2020 | -0.9849 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2020 | 2020 | -0.9849 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1519 | 1519 | -1.2032 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1140 | 1140 | -1.2833 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 979 | 979 | -1.4756 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 909 | 909 | -0.5222 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 751 | 751 | -1.7863 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 674 | 674 | -0.8984 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 577 | 577 | 0.5506 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 511 | 511 | -0.5086 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 446 | 446 | -0.54 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 397 | 397 | -1.1845 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 396 | 396 | -1.7112 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 347 | 347 | -0.9078 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 330 | 330 | -1.2378 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 307 | 307 | -2.4276 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 4384 | 238 | -0.1342 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 238 | 238 | -0.1342 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 238 | 238 | -0.1342 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 228 | 228 | 0.2462 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 192 | 192 | 0.077 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 188 | 188 | 0.7061 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 116 | 116 | 2.3485 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 114 | 114 | -1.6474 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 92 | 92 | -0.9537 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 85 | 85 | -0.3501 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 79 | 79 | 0.128 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 67 | 67 | 1.0949 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 60 | 60 | -0.289 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 59 | 59 | 0.3197 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 55 | 55 | 0.7728 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 54 | 54 | 0.2328 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 47 | 47 | 2.4159 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 43 | 43 | 0.994 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 42 | 42 | -0.4983 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -0.4387 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 796, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 182812 | 182812 | None | -0.5005 | 0.2042 | `hold_sample` |
| `arm` | `AVG_DOWN` | 145253 | 144633 | None | -0.7964 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 104120 | 104120 | None | -0.5034 | 0.2007 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 101348 | 100728 | None | -0.9586 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 43905 | 43905 | None | -0.4241 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 39576 | 38212 | None | 0.6206 | 0.9777 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 39576 | 38212 | None | 0.6206 | 0.9777 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 33837 | 33837 | None | -0.4653 | 0.2166 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 32308 | 32308 | None | 0.5155 | 0.9815 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 23796 | 23796 | None | -0.5116 | 0.2095 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 18480 | 18480 | None | -0.3262 | 0.1617 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 11729 | 11729 | None | -0.5089 | 0.1942 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9330 | 9330 | None | -0.5567 | 0.1977 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4044 | 4044 | None | -0.4616 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2328 | 2328 | None | -0.835 | 0.0842 | `hold_sample` |
| `blocker_reason` | `ok` | 1532 | 1532 | None | -2.3653 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1458 | 1458 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1438 | 1438 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1303 | 1303 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 1283 | 1283 | None | -0.3266 | 0.1808 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 476 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 238 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 476 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 238 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 476 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 238 | 238 | -0.1342 | -0.1789 | 0.3319 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 472 | 236 | -0.1339 | -0.1785 | 0.3347 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 342 | 171 | -0.0748 | -0.0997 | 0.3626 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 318 | 159 | -0.6628 | -0.8838 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 92 | 92 | -0.9537 | -1.2716 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 184 | 92 | -0.9537 | -1.2716 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 134 | 67 | -0.2859 | -0.3812 | 0.2537 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 60 | 60 | -0.289 | -0.3853 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 120 | 60 | -0.289 | -0.3853 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 54 | 54 | 0.2328 | 0.3104 | 0.8704 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 108 | 54 | 0.2328 | 0.3104 | 0.8704 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 94 | 47 | 0.274 | 0.3653 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 17 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 34 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 34 | 17 | 0.8713 | 1.1618 | 1.0 | `hold_sample` |

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
