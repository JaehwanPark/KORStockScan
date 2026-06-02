# Lifecycle Decision Matrix - 2026-06-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-02_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `46138`
- source_rows_total: `82768`
- retained_rows: `46138`
- dropped_rows_by_source: `{}`
- joined_rows: `43983`
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
- lifecycle_flow_bucket_count: `208`
- lifecycle_flow_complete_count: `221`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0052`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1708 | 396 | 1.675 | 1.0 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 799 | 713 | -0.5017 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 758 | 713 | -0.8532 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 40855 | 40851 | -0.3913 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2018 | 1310 | -0.9422 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 208, 'complete_flow_count': 221, 'incomplete_flow_count': 42660, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 31384 | 31381 | -0.6641 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 8862 | 8861 | 0.6073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 552 | 552 | -1.0823 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 162 | 162 | 2.0221 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 117 | 117 | 2.6659 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 26 | 26 | -0.3942 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 25 | 25 | 1.7369 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:93f13405b3` | 12 | 12 | -0.9184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:07dd4b972c` | 11 | 11 | -0.5823 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7c897ec6ef` | 9 | 9 | -2.2716 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b72b8d0720` | 8 | 8 | -1.5616 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:438a0575a6` | 8 | 8 | -0.2371 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 8 | 8 | -0.8125 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3799fc10bf` | 7 | 7 | -0.6467 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 7 | 7 | -0.7771 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1905c4a9b7` | 5 | 5 | 1.2181 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 5 | 5 | -0.4185 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 5 | 5 | -1.024 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:cbc2ec64ca` | 4 | 4 | 0.6865 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:f10228dfd1` | 4 | 4 | -1.7412 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 239, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 304 | 304 | 2.2464 | 3.6109 | 0.6283 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1616 | 304 | 2.2464 | 3.6109 | 0.6283 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 999 | 304 | 2.2464 | 3.6109 | 0.6283 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 304 | 304 | 2.2464 | 3.6109 | 0.6283 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 304 | 304 | 2.2464 | 3.6109 | 0.6283 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 306 | 247 | 2.194 | 3.5403 | 0.6357 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 463 | 183 | 1.7365 | 2.9585 | 0.6066 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_proxy_normal` | 157 | 157 | 2.3093 | 3.6014 | 0.6242 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 173 | 122 | 2.5777 | 4.0551 | 0.6147 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 709 | 92 | -0.213 | -0.6841 | 0.3696 | `hold_no_edge` |
| `strength_bucket` | `risk_unknown` | 462 | 92 | -0.213 | -0.6841 | 0.3696 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 462 | 92 | -0.213 | -0.6841 | 0.3696 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 545 | 90 | -0.2054 | -0.6494 | 0.3778 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_watch` | 83 | 83 | 2.226 | 3.6963 | 0.6145 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 412 | 80 | -0.0537 | -0.4954 | 0.4125 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 678 | 73 | -0.1448 | -0.8658 | 0.3287 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 235 | 62 | 2.2472 | 3.4234 | 0.6452 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 207 | 57 | 2.0843 | 3.3663 | 0.7368 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 799 | 44 | -0.2608 | -1.1011 | 0.2954 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 128 | 43 | 2.0678 | 3.3106 | 0.5582 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 39 | 39 | -0.2192 | -1.8761 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 38 | 38 | 2.273 | 3.708 | 0.6842 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 107 | 35 | 1.1799 | 1.6072 | 0.6286 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 34 | 34 | 0.213 | 1.7844 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 32 | 32 | 2.7554 | 4.3129 | 0.6563 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 31 | 31 | 2.9706 | 4.6965 | 0.6451 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 159 | 21 | 0.8019 | 0.9486 | 0.6667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 21 | 21 | 1.2481 | 2.2122 | 0.6191 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 20 | 20 | 2.4167 | 3.6153 | 0.65 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 23 | 19 | -0.4751 | 0.0136 | 0.5263 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 19 | 19 | 2.5353 | 4.3485 | 0.6842 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 17 | 17 | 0.3271 | 0.3361 | 0.5294 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 46 | 11 | -1.4338 | -1.8727 | 0.0909 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 880 | 863 | -0.4997 | `keep_collecting` |
| `actual_order_submitted` | `false` | 887 | 728 | -0.5156 | `keep_collecting` |
| `actual_order_submitted` | `true` | 801 | 716 | -0.506 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 727 | 713 | -0.5017 | `keep_collecting` |
| `latency_state` | `simulated` | 727 | 713 | -0.5017 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 709 | 695 | -0.4827 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 741 | 674 | -0.3996 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 623 | 610 | -0.4759 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 574 | 563 | -0.5049 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 595 | 562 | -0.5028 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 573 | 562 | -0.5028 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 474 | 467 | -0.5007 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 442 | 433 | -0.4306 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 376 | 368 | -0.346 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 332 | 326 | -0.6423 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 278 | 274 | -0.449 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 261 | 257 | -0.6102 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 226 | 220 | -0.451 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 196 | 190 | -0.3749 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 154 | 151 | -0.4979 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 135 | 132 | -0.3886 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 104 | 103 | -0.655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 94 | 91 | -0.2595 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 73 | 73 | -0.2932 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 43 | 38 | -2.2815 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 24 | 23 | -0.6284 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 23 | 23 | -0.4078 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 18 | 18 | -1.2345 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 91 | 18 | -1.2345 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 18 | 18 | -1.2345 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 13 | 13 | -1.3158 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -0.8555 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -3.6731 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_lt1s` | 6 | 6 | -0.6541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -3.3178 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.0876 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -2.5133 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=true|submitted=false` | 3 | 3 | -1.5309 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.8499 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 2 | 2 | 0.7144 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 727 | 713 | -0.8532 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 727 | 713 | -0.8532 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 510 | 501 | -1.4148 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 447 | 438 | -0.7992 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 303 | 303 | -1.358 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 267 | 262 | -0.9444 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 187 | 187 | -1.5061 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 65 | 64 | 0.0721 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 69 | 61 | 0.0694 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 50 | 48 | 0.828 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 40 | 40 | 0.14 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 38 | 38 | -0.0186 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 31 | 31 | 0.889 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 30 | 29 | 1.9316 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 25 | 25 | 0.1102 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 21 | 21 | -0.0652 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 19 | 19 | 1.6712 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 17 | 17 | 0.7169 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 13 | 13 | -0.833 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.4266 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 20 | 10 | -0.4095 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 2.4408 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 7 | 7 | -0.3964 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.44 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 2.5685 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.2951 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 31 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 67, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 953 | 953 | -1.3226 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 677 | 677 | -0.894 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 602 | 602 | -1.0433 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 602 | 602 | -1.0433 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 602 | 602 | -1.0433 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 455 | 455 | -1.2265 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 277 | 277 | -1.4074 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 247 | 247 | -1.2274 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 244 | 244 | -0.3663 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 224 | 224 | -1.7198 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 182 | 182 | 0.4582 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 156 | 156 | -0.8078 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 149 | 149 | -0.533 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 138 | 138 | -0.5515 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 101 | 101 | -2.3282 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 91 | 91 | -1.101 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 88 | 88 | -1.6447 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 85 | 85 | -0.8366 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 74 | 74 | -1.1802 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 66 | 66 | 0.0877 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 66 | 66 | 0.1052 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 62 | 62 | -0.0295 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 47 | 47 | 0.8101 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 32 | 32 | -1.5593 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 739 | 31 | -0.0295 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 29 | 29 | 1.8898 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 29 | 29 | -0.5395 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 24 | 24 | 0.7872 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 20 | 20 | -0.4947 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 18 | 18 | -0.0153 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 17 | 17 | -0.3463 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 17 | 17 | 1.064 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 17 | 17 | 1.5477 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 15 | 15 | 0.7293 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 15 | 15 | 0.0768 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 10 | 10 | -0.3053 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -0.3136 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 10 | 10 | 0.0439 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 9 | 9 | -0.7808 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 8 | 8 | 0.1481 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 245, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 53746 | 53740 | -0.7268 | -0.8031 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 40851 | 40851 | -0.3913 | -0.4603 | 0.2134 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 21288 | 21288 | -0.3807 | -0.4545 | 0.2316 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 17776 | 17774 | 0.6071 | 0.5533 | 0.9811 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 10188 | 10188 | -0.3634 | -0.4209 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 7501 | 7501 | -0.3752 | -0.4339 | 0.1864 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 7196 | 7196 | 0.5664 | 0.5126 | 0.9873 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 6594 | 6594 | -0.293 | -0.3125 | 0.1806 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 5364 | 5364 | -0.4929 | -0.5574 | 0.1764 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 3858 | 3858 | -0.3616 | -0.4366 | 0.2263 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 2840 | 2840 | -0.3614 | -0.4233 | 0.2011 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1265 | 1265 | -0.4275 | -0.4572 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 709 | 709 | -0.9032 | -0.9032 | 0.0451 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 353 | 353 | -1.8637 | -2.3507 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 333 | 333 | -0.863 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 317 | 317 | 2.5505 | 2.5644 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_cutoff` | 290 | 290 | -0.1455 | -0.1643 | 0.2551 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 269 | 269 | -0.6772 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 266 | 266 | -0.6988 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 238 | 238 | -0.738 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 214 | 214 | -0.6559 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 214 | 214 | -0.9728 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 206 | 206 | -0.7709 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 203 | 203 | -0.6947 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 199 | 199 | -1.1839 | -1.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 196 | 196 | -0.8815 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 194 | 194 | -0.6543 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 193 | 193 | -1.0402 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 192 | 192 | -0.9549 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 191 | 191 | -0.7259 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 190 | 190 | -0.7316 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 185 | 185 | -0.8492 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 184 | 184 | -0.7828 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 179 | 179 | -0.8232 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 172 | 172 | -0.871 | -0.97 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 172 | 172 | -1.1065 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 171 | 171 | -0.8964 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 170 | 170 | -0.7117 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 169 | 169 | -0.6248 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 168 | 168 | -0.7608 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 93 | 62 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 62 | 31 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `stage` | `exit` | 31 | 31 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 62 | 31 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 62 | 31 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 31 | 31 | -0.0295 | -0.0393 | 0.3548 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 38 | 19 | -0.5305 | -0.7074 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 36 | 18 | 0.0146 | 0.0195 | 0.3333 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 13 | -0.0905 | -0.1208 | 0.3846 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 10 | 10 | -0.3053 | -0.407 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 20 | 10 | -0.3053 | -0.407 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -0.7808 | -1.0411 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -0.7808 | -1.0411 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 8 | 8 | 0.1481 | 0.1975 | 0.875 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 16 | 8 | 0.1481 | 0.1975 | 0.875 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 16 | 8 | 0.1481 | 0.1975 | 0.875 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 2 | 2 | 1.7288 | 2.305 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300` | 4 | 2 | 1.7288 | 2.305 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 4 | 2 | 1.7288 | 2.305 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.6975 | 0.93 | 1.0 | `hold_sample` |

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
