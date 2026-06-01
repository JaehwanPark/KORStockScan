# Lifecycle Decision Matrix - 2026-06-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-01_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `160540`
- source_rows_total: `179335`
- retained_rows: `160540`
- dropped_rows_by_source: `{}`
- joined_rows: `154581`
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
- lifecycle_flow_bucket_count: `318`
- lifecycle_flow_complete_count: `273`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4269 | 626 | 0.9605 | 0.9398 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1559 | 1132 | -0.7316 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1481 | 1132 | -0.8153 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 147883 | 147742 | -0.32 | 0.9999 | `pass` | `NO_CHANGE` | False |
| `exit` | 5348 | 3949 | -0.6339 | 0.9996 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 318, 'complete_flow_count': 273, 'incomplete_flow_count': 45617, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 67354 | 67299 | -0.6336 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 20314 | 20301 | 0.6092 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 529 | 529 | -0.8355 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 260 | 260 | -0.4312 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 199 | 199 | 1.1369 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 118 | 118 | 1.5523 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 83 | 83 | -0.4989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 80 | 80 | -0.4405 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 57 | 57 | -0.1179 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 53 | 53 | -0.1351 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 112 | 32 | -1.5546 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 26 | 26 | 0.6525 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 646 | 22 | -1.0451 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 19 | 19 | -0.7663 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 16 | 16 | -0.4431 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 16 | 16 | -0.3538 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 13 | 13 | -0.6131 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:34cc4a9d10` | 12 | 12 | -0.0461 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 312, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `exit_unknown` | 4116 | 473 | 1.5224 | 2.5484 | 0.5602 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 1818 | 473 | 1.5224 | 2.5484 | 0.5602 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 473 | 473 | 1.5224 | 2.5484 | 0.5602 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 343 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 343 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 1034 | 333 | 1.0816 | 2.1134 | 0.5436 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 489 | 292 | 1.3376 | 2.3085 | 0.5377 | `hold_sample` |
| `liquidity_bucket` | `liquidity_unknown` | 3230 | 283 | 0.6181 | 1.223 | 0.47 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 2382 | 255 | 0.8429 | 1.5101 | 0.4902 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 175 | 175 | 1.2604 | 2.0603 | 0.5486 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 280 | 172 | 1.5229 | 2.4222 | 0.5523 | `hold_sample` |
| `strength_bucket` | `risk_unknown` | 1857 | 153 | -0.7765 | -0.8464 | 0.3399 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1856 | 153 | -0.7765 | -0.8464 | 0.3399 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 1905 | 145 | -0.744 | -0.7597 | 0.3586 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `strength_bucket` | `strength_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 942 | 123 | -0.1841 | 0.2061 | 0.4553 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2358 | 99 | -0.5785 | -1.0538 | 0.2828 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_watch` | 88 | 88 | 1.4491 | 2.4486 | 0.5341 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 70 | 70 | -0.4163 | -1.909 | 0.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 2221 | 69 | -0.6347 | -1.1687 | 0.2753 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 614 | 58 | -0.3008 | -0.3141 | 0.3793 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 56 | 56 | 1.0461 | 2.0498 | 0.5357 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 78 | 54 | -1.1394 | -0.4659 | 0.4444 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | -0.885 | 1.6091 | 1.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 31 | 31 | 1.3635 | 2.2739 | 0.5484 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 29 | 29 | -0.1743 | -0.3874 | 0.5517 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 228 | 27 | -1.4996 | -1.3426 | 0.2963 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 27 | 27 | -0.8735 | -1.2426 | 0.4444 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 76, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1635 | 1346 | -0.7247 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1741 | 1156 | -0.7276 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1564 | 1134 | -0.7314 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1404 | 1132 | -0.7316 | `keep_collecting` |
| `latency_state` | `simulated` | 1404 | 1132 | -0.7316 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1372 | 1106 | -0.736 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1387 | 1034 | -0.6013 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1250 | 1021 | -0.7033 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1173 | 918 | -0.7418 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1209 | 913 | -0.7367 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1168 | 913 | -0.7367 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 944 | 706 | -0.5831 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 844 | 629 | -0.5245 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 787 | 623 | -0.7253 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 557 | 474 | -0.7359 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 522 | 472 | -1.014 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 626 | 471 | -0.5878 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 406 | 377 | -1.006 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 369 | 306 | -0.5364 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 236 | 219 | -0.7106 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 201 | 190 | -0.7096 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 161 | 111 | -0.9923 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 115 | 93 | -2.129 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 92 | -0.5441 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 94 | 76 | -0.9607 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 60 | 58 | -0.5724 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 54 | 49 | -0.7609 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 31 | 31 | -2.4145 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 39 | 26 | -0.544 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 206 | 26 | -0.544 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 39 | 26 | -0.544 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 27 | 26 | -1.6756 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 27 | 21 | -0.6372 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 14 | 14 | -3.8028 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -0.457 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 5 | 5 | -1.6833 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 5 | -1.558 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -3.4759 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 5 | 4 | -0.4715 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_lt1s` | 4 | 4 | -1.402 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 71, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_source_stage` | `scalp_sim_holding_started` | 1411 | 1132 | -0.8153 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 741 | 740 | -0.7359 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 723 | 709 | -1.5401 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 882 | 670 | -0.7206 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 670 | 392 | -0.9653 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 280 | 280 | -1.4919 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 264 | 263 | -0.8883 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 252 | 175 | -1.0868 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 172 | 172 | -1.6186 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 132 | 132 | -1.5007 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 129 | 124 | 0.1482 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 129 | 114 | -0.1796 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 106 | 106 | -1.6377 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 116 | 104 | 0.6358 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 66 | 62 | 1.8273 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 56 | 56 | 0.7777 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 49 | 49 | 0.2623 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 44 | 44 | 0.0561 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 30 | 30 | 1.8399 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 30 | 30 | 0.0278 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 26 | 26 | 0.2199 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 26 | 26 | -0.4381 | `source_quality_workorder` |
| `holding_action` | `BUY` | 38 | 24 | -0.681 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 24 | 24 | -0.2238 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.6988 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.3091 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 39 | 19 | -0.4376 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 17 | 17 | 2.1414 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 17 | 17 | -0.2719 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 15 | 15 | 0.7207 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 12 | 12 | -0.2423 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -0.9327 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 9 | 9 | -1.6396 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 9 | 9 | -0.3488 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 7 | 7 | 1.7258 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.7605 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 5 | 5 | 1.0928 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.3133 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.799 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 2 | 2 | 0.9238 | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 93, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2766 | 2766 | -0.5943 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2766 | 2766 | -0.5943 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1896 | 1896 | -1.3108 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3010 | 1611 | -0.4776 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1281 | 1281 | -0.6439 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 1211 | 1211 | -0.4716 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1057 | 1057 | -0.86 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 702 | 702 | -0.4768 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 635 | 635 | -1.2004 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 553 | 553 | -1.1699 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 468 | 468 | -0.48 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 442 | 442 | -1.4072 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 398 | 398 | 0.137 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 349 | 349 | -1.2774 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 347 | 347 | -0.2145 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 342 | 342 | 0.37 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 319 | 319 | -1.8955 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 268 | 268 | -0.7934 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 212 | 212 | 0.3929 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 187 | 187 | 0.4938 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 173 | 173 | 1.2093 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 164 | 164 | 0.2547 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 152 | 152 | -2.5124 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 129 | 129 | -1.1274 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 122 | 122 | -1.7837 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 114 | 114 | 0.2837 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 113 | 113 | -1.212 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 97 | 97 | -0.8526 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 84 | 84 | 2.3449 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 53 | 53 | -1.6209 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 47 | 47 | -0.5352 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 44 | 44 | -0.0481 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 43 | 43 | 0.7676 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 38 | 38 | -0.5259 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 31 | 31 | 1.1448 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 28 | 28 | 1.145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 28 | 28 | 2.0529 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 27 | 27 | 1.1184 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 27 | 27 | 1.3681 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 387, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 142482 | 142372 | -0.7454 | -0.8179 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 103362 | 103362 | -0.2866 | -0.3282 | 0.264 | `hold_no_edge` |
| `ai_score_source` | `ai_source_unknown` | 83726 | 83634 | -0.3791 | -0.4281 | 0.2298 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 64107 | 64107 | -0.243 | -0.2898 | 0.287 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 56774 | 56602 | 0.7351 | 0.6915 | 0.9848 | `hold_sample` |
| `arm` | `arm_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 23078 | 23078 | -0.3545 | -0.4241 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20482 | 20482 | -0.0446 | -0.0268 | 0.352 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 17152 | 17152 | -0.2984 | -0.3392 | 0.2479 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 17036 | 17036 | 0.5767 | 0.5225 | 0.9898 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 14406 | 14406 | -0.2932 | -0.3182 | 0.2028 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 14050 | 14050 | -0.2633 | -0.293 | 0.2172 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 7404 | 7404 | -0.9294 | -1.121 | 0.2277 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 5773 | 5773 | -0.3402 | -0.386 | 0.2326 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 3395 | 3395 | -0.3658 | -0.3897 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 955 | 955 | -0.3664 | -0.3861 | 0.1183 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 729 | 729 | 2.6981 | 2.7145 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 583 | 583 | -5.2678 | -6.5804 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 560 | 560 | -0.7306 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 547 | 547 | -0.6611 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 534 | 534 | -0.7363 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 501 | 501 | -0.7575 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 488 | 488 | -0.0149 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 472 | 472 | -0.0354 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 470 | 470 | -0.7167 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 469 | 469 | -0.0422 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 463 | 463 | -0.8661 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 461 | 461 | -0.6854 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 425 | 425 | -0.8258 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 425 | 425 | -0.9707 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 411 | 411 | -0.8925 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 403 | 403 | -0.7081 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 401 | 401 | -0.9521 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 400 | 400 | -0.8408 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 391 | 391 | -1.0643 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 389 | 389 | -0.6595 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 375 | 375 | -1.1139 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 372 | 372 | -0.7621 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 266 | 196 | 0.3744 | 0.4992 | 0.449 | `hold_sample` |
| `stage` | `exit` | 126 | 126 | 0.3935 | 0.5246 | 0.4524 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 196 | 126 | 0.3935 | 0.5246 | 0.4524 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 187 | 120 | 0.4218 | 0.5623 | 0.475 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 140 | 70 | 0.3401 | 0.4534 | 0.4428 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 70 | 70 | 0.3401 | 0.4534 | 0.4428 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 116 | 58 | 0.4199 | 0.5598 | 0.4655 | `hold_sample` |
| `overnight_action` | `action_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `confidence_band` | `confidence_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `held_bucket` | `held_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 76 | 38 | -0.4196 | -0.5595 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 56 | 36 | -0.2406 | -0.3208 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 40 | 25 | 0.1221 | 0.1628 | 0.64 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 38 | 24 | -0.7684 | -1.0246 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 35 | 23 | 1.6673 | 2.223 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 20 | 20 | -0.246 | -0.328 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 16 | 16 | -0.2339 | -0.3119 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 15 | 15 | 0.1295 | 0.1727 | 0.6667 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 14 | 14 | -0.7709 | -1.0279 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 22 | 11 | 0.1977 | 0.2636 | 0.9091 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 10 | 10 | -0.765 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.111 | 0.148 | 0.6 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 8 | 3.4725 | 4.63 | 1.0 | `candidate_recovery_or_relax` |

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
