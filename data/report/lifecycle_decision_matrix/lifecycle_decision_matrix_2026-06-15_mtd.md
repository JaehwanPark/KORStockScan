# Lifecycle Decision Matrix - 2026-06-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-15_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `142503`
- source_rows_total: `225194`
- retained_rows: `142503`
- dropped_rows_by_source: `{}`
- joined_rows: `131098`
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
- lifecycle_flow_bucket_count: `605`
- lifecycle_flow_complete_count: `658`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0051`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 6489 | 1012 | 0.4212 | 0.9637 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3060 | 2052 | -0.564 | 0.9972 | `pass` | `NO_CHANGE` | False |
| `holding` | 2876 | 2052 | -0.9456 | 0.9969 | `pass` | `EXIT` | False |
| `scale_in` | 123198 | 122278 | -0.4425 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6880 | 3704 | -0.9677 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 605, 'complete_flow_count': 658, 'incomplete_flow_count': 129312, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 95004 | 94653 | -0.7434 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 26623 | 26054 | 0.6744 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1333 | 1333 | -1.0737 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 203 | 203 | 1.3749 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 156 | 156 | 1.2545 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 128 | 128 | 1.1101 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 102 | 102 | -0.2522 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 40 | 40 | -0.9057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 26 | 26 | -0.8966 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 22 | 22 | -0.8464 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 12 | 12 | -1.145 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 9 | 9 | -1.8072 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 9 | 9 | -0.9933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 9 | 9 | -0.2825 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.5857 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 382, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4069 | 1010 | 0.4235 | 0.423 | 0.4366 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 3667 | 705 | 0.4086 | -0.0068 | 0.417 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 4199 | 499 | -0.3525 | -1.2332 | 0.2405 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 487 | 487 | 1.2667 | 2.157 | 0.6345 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 5964 | 487 | 1.2667 | 2.157 | 0.6345 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2495 | 438 | -0.3561 | -1.2563 | 0.2397 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 2889 | 437 | -0.356 | -1.2616 | 0.238 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 2672 | 432 | -0.1549 | -0.917 | 0.287 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1770 | 373 | 0.8591 | 1.5273 | 0.6086 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 373 | 373 | 0.8591 | 1.5273 | 0.6086 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1778 | 347 | 0.3026 | 0.1763 | 0.4553 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 650 | 336 | 0.7299 | 1.2528 | 0.5655 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 2659 | 281 | -0.3857 | -1.2401 | 0.2313 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 251 | 251 | -0.2738 | -1.981 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1333 | 222 | 0.4422 | 0.3525 | 0.4324 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 1375 | 176 | -0.0208 | -0.2569 | 0.3409 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 391 | 162 | 0.5814 | 1.178 | 0.5802 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 473 | 146 | 0.59 | 0.8251 | 0.4863 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 430 | 143 | 0.177 | 1.7955 | 0.5105 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 616 | 137 | 0.6759 | 0.7804 | 0.4526 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 128 | 128 | -0.6557 | 1.8186 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 59 | 59 | 0.7906 | 1.1097 | 0.6271 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 97, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 2955 | 2052 | -0.564 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2720 | 2052 | -0.564 | `keep_collecting` |
| `latency_state` | `simulated` | 2720 | 2052 | -0.564 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 2947 | 2052 | -0.564 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2682 | 2024 | -0.5484 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2498 | 1901 | -0.5912 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2219 | 1689 | -0.5841 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2201 | 1660 | -0.616 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1709 | 1295 | -0.6896 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1547 | 1200 | -0.6981 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1455 | 1200 | -0.6981 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1455 | 1200 | -0.6981 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1551 | 1186 | -0.6138 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1498 | 1157 | -0.6175 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1233 | 852 | -0.3749 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1233 | 852 | -0.3749 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1040 | 779 | -0.4406 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 899 | 709 | -0.5643 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 993 | 687 | -0.3616 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 841 | 685 | -0.7604 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 775 | 598 | -0.3821 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 663 | 465 | -0.36 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 504 | 364 | -0.2398 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 501 | 363 | -0.4701 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 291 | 246 | -0.5846 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 303 | 205 | -0.4063 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 190 | 166 | -0.3186 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 222 | 151 | -0.2213 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 594 | 151 | -0.2213 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 222 | 151 | -0.2213 | `keep_collecting` |
| `would_limit_fill` | `false` | 561 | 150 | -0.2232 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 200 | 134 | -0.0486 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 180 | 115 | -0.8658 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 46 | 39 | -2.0609 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 39 | 31 | -0.7382 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 38 | 28 | -1.6902 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 38 | 28 | -1.6902 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 21 | 16 | -1.6853 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 16 | -0.7283 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 18 | 14 | -2.6878 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2720 | 2052 | -0.9456 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2720 | 2052 | -0.9456 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1586 | 1522 | -1.4389 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1740 | 1295 | -1.0526 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 975 | 975 | -1.5187 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 826 | 632 | -0.6963 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 440 | 440 | -1.2627 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 183 | 170 | 0.2043 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 137 | 131 | 0.5113 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 154 | 125 | -1.0978 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 147 | 117 | 0.0223 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 107 | 107 | -1.4358 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 107 | 107 | 0.0883 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 81 | 81 | -0.0077 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 84 | 80 | 1.9709 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 75 | 75 | 0.3756 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 61 | 61 | 0.3872 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 46 | 46 | 0.6713 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 41 | 41 | 2.1033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 35 | 35 | 0.0561 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 34 | 34 | 1.9376 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 71 | 32 | -0.3884 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 16 | 16 | -0.4274 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 16 | 16 | -0.3494 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.111 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 156 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 55 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 101 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 668 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 156 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 29 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 194 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 445 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 42 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 17 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2784 | 2784 | -1.334 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1992 | 1992 | -0.9961 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1556 | 1556 | -1.0083 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1556 | 1556 | -1.0083 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1556 | 1556 | -1.0083 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1199 | 1199 | -1.2042 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 876 | 876 | -1.3142 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 761 | 761 | -1.4908 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 726 | 726 | -0.5417 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 565 | 565 | -1.7925 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 505 | 505 | -0.9036 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 460 | 460 | 0.4719 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 365 | 365 | -0.5188 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 321 | 321 | -0.5464 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 319 | 319 | -1.7426 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 279 | 279 | -1.2236 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 278 | 278 | -0.9135 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 255 | 255 | -1.2919 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 226 | 226 | -2.385 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 174 | 174 | 0.2104 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 158 | 158 | 0.0418 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3332 | 156 | -0.1996 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 156 | 156 | -0.1996 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 156 | 156 | -0.1996 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 138 | 138 | 0.626 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 85 | 85 | 2.2289 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 84 | 84 | -0.5085 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 84 | 84 | -1.7183 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 64 | 64 | -1.0035 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 64 | 64 | -0.4271 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 56 | 56 | 0.0087 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 51 | 51 | 1.0081 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 47 | 47 | 0.2967 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 44 | 44 | 0.7965 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 41 | 41 | -0.5096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 39 | 39 | -0.3135 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -0.4419 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 38 | 38 | 2.2485 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 36 | 36 | 0.4157 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 30 | 30 | 0.2672 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 604, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 122266 | 122266 | None | -0.5157 | 0.2096 | `hold_sample` |
| `arm` | `AVG_DOWN` | 96465 | 96114 | None | -0.8218 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 68465 | 68114 | None | -0.9843 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 62049 | 62049 | None | -0.5238 | 0.2064 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 28000 | 28000 | None | -0.4265 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 26733 | 26164 | None | 0.6093 | 0.98 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 26733 | 26164 | None | 0.6093 | 0.98 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 24004 | 24004 | None | -0.4615 | 0.2307 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 22841 | 22841 | None | 0.5322 | 0.982 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 19554 | 19554 | None | -0.5259 | 0.2099 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 9758 | 9758 | None | -0.3179 | 0.1824 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 9087 | 9087 | None | -0.524 | 0.1897 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 7572 | 7572 | None | -0.5851 | 0.1925 | `hold_sample` |
| `blocker_reason` | `low_broken` | 2845 | 2845 | None | -0.4626 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1783 | 1783 | None | -0.8556 | 0.0768 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1270 | 1270 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1141 | 1141 | None | -2.3603 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1083 | 1083 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 1081 | 1081 | None | -0.82 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 1010 | 1010 | None | -0.78 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 312 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 156 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 312 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 156 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 312 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 312 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 156 | 156 | -0.1996 | -0.2661 | 0.3141 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 214 | 107 | -0.7159 | -0.9546 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 202 | 101 | -0.175 | -0.2333 | 0.3267 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 64 | 64 | -1.0035 | -1.338 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 128 | 64 | -1.0035 | -1.338 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 110 | 55 | -0.2448 | -0.3264 | 0.2909 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 39 | 39 | -0.3135 | -0.4179 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 78 | 39 | -0.3135 | -0.4179 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 30 | 30 | 0.2672 | 0.3563 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 60 | 30 | 0.2672 | 0.3563 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 52 | 26 | 0.3144 | 0.4192 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 13 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |

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
