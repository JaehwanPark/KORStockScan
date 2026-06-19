# Lifecycle Decision Matrix - 2026-06-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-19_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `151308`
- source_rows_total: `209705`
- retained_rows: `151308`
- dropped_rows_by_source: `{}`
- joined_rows: `136300`
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
- lifecycle_flow_bucket_count: `702`
- lifecycle_flow_complete_count: `772`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 8530 | 1117 | 0.6455 | 0.9619 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3137 | 1891 | -0.5353 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 2933 | 1891 | -0.921 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 130288 | 128307 | -0.4587 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6420 | 3094 | -0.9281 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 702, 'complete_flow_count': 772, 'incomplete_flow_count': 136679, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 103125 | 102508 | -0.7281 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 25821 | 24457 | 0.6867 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1099 | 1099 | -1.0207 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 225 | 225 | 1.6047 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 209 | 209 | 1.6218 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 124 | 124 | 1.5284 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 90 | 90 | -0.1833 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 41 | 41 | -0.8961 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 34 | 34 | -0.8147 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 19 | 19 | -0.9811 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 14 | 14 | -2.1294 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 12 | 12 | -0.2913 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 11 | 11 | -0.4076 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 10 | 10 | -0.9068 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 10 | 10 | 0.8892 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 10 | 10 | -1.281 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 9 | 9 | -0.5166 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 428, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6086 | 1112 | 0.6397 | 0.6274 | 0.4442 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 6049 | 880 | 0.542 | 0.1847 | 0.4284 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 563 | 563 | 1.5972 | 2.5187 | 0.6501 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 7976 | 563 | 1.5972 | 2.5187 | 0.6501 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 6400 | 513 | -0.3095 | -1.3057 | 0.2339 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4353 | 470 | -0.3455 | -1.3205 | 0.2276 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 4591 | 458 | -0.36 | -1.3029 | 0.2314 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 4691 | 456 | -0.1024 | -0.875 | 0.2763 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1681 | 430 | 1.4119 | 2.2742 | 0.6302 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 430 | 430 | 1.4119 | 2.2742 | 0.6302 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 931 | 407 | 1.2157 | 1.8368 | 0.5799 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 2024 | 351 | 0.6288 | 0.7068 | 0.4587 | `hold_no_edge` |
| `score_band` | `score_70p` | 834 | 292 | 1.1401 | 1.7894 | 0.5924 | `hold_no_edge` |
| `score_band` | `score_60_62` | 4159 | 284 | -0.35 | -1.434 | 0.2042 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 265 | 265 | -0.2057 | -1.9742 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1284 | 221 | 0.6829 | 0.4635 | 0.4208 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 376 | 181 | 1.277 | 1.8687 | 0.5801 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 145 | 145 | -0.2879 | -2.9642 | 0.0 | `hold_no_edge` |
| `score_band` | `score_63_65` | 649 | 128 | 0.3903 | 0.5681 | 0.4297 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 127 | 127 | -0.6954 | 2.0056 | 1.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 640 | 114 | 1.3425 | 1.8667 | 0.5351 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 113 | 113 | 1.393 | 2.0898 | 0.7257 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 1250 | 113 | -0.6678 | -1.2465 | 0.239 | `hold_no_edge` |
| `overbought_bucket` | `overbought_ok` | 418 | 104 | 0.7367 | 2.9036 | 0.4808 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 399 | 98 | 0.3762 | -1.1022 | 0.2755 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 957 | 84 | -0.1402 | -1.3226 | 0.2024 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 74 | 74 | 1.1078 | 1.5323 | 0.5946 | `hold_no_edge` |
| `score_band` | `score_lt60` | 1451 | 72 | -0.2134 | -1.0042 | 0.3056 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 833 | 71 | -0.387 | -1.4062 | 0.1831 | `hold_no_edge` |
| `strength_bucket` | `neutral_strength_momentum` | 444 | 37 | -0.091 | 0.2334 | 0.4324 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 164, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3040 | 1891 | -0.5353 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2753 | 1891 | -0.5353 | `keep_collecting` |
| `latency_state` | `simulated` | 2753 | 1891 | -0.5353 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3029 | 1891 | -0.5353 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2720 | 1869 | -0.5219 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2508 | 1735 | -0.5564 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2277 | 1571 | -0.5643 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2217 | 1522 | -0.5866 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1656 | 1164 | -0.5997 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1481 | 1020 | -0.7493 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1452 | 1017 | -0.692 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1344 | 1017 | -0.692 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1344 | 1017 | -0.692 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1333 | 949 | -0.6988 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1377 | 874 | -0.3529 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1377 | 874 | -0.3529 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1246 | 845 | -0.3381 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1011 | 707 | -0.2738 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1115 | 705 | -0.3272 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 816 | 533 | -0.5284 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 632 | 462 | -0.9283 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 603 | 377 | -0.3918 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 519 | 347 | -0.2384 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 590 | 320 | -0.3928 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 191 | 165 | -0.5202 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 245 | 156 | -0.3009 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 595 | 156 | -0.3009 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 245 | 156 | -0.3009 | `keep_collecting` |
| `would_limit_fill` | `false` | 628 | 155 | -0.3031 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 249 | 138 | -0.4861 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 131 | -0.6711 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 176 | 125 | 0.0233 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 184 | 114 | -0.13 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 133 | 106 | -0.3329 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2753 | 1891 | -0.921 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2753 | 1891 | -0.921 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1471 | 1406 | -1.4311 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1575 | 1073 | -1.04 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 811 | 811 | -1.4785 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1036 | 711 | -0.6995 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 503 | 503 | -1.3373 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 159 | 145 | 0.2298 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 139 | 131 | 0.6257 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 142 | 107 | -1.1991 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 92 | 92 | -1.5259 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 137 | 89 | 0.0137 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 82 | 82 | 0.15 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 83 | 80 | 2.1163 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 64 | 64 | 0.4482 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 63 | 63 | -0.0636 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 61 | 61 | 0.8344 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 60 | 60 | 0.3342 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 42 | 42 | 2.61 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 82 | 40 | -0.3823 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 34 | 34 | 1.5527 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 24 | 24 | 0.1409 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 21 | 21 | -0.4134 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 19 | 19 | -0.3479 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.3963 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.7229 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.3238 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 180 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 45 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 135 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 862 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 180 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 325 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 502 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 48 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 38 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 68, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2289 | 2289 | -1.3228 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1589 | 1589 | -1.0086 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1325 | 1325 | -0.9447 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1325 | 1325 | -0.9447 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1325 | 1325 | -0.9447 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 974 | 974 | -1.1827 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 743 | 743 | -1.2871 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 622 | 622 | -1.4338 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 523 | 523 | -0.5614 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 459 | 459 | -1.8055 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 444 | 444 | -0.9398 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 353 | 353 | -0.5076 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 333 | 333 | 0.6092 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 310 | 310 | -0.5357 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 280 | 280 | -1.1655 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 265 | 265 | -1.6786 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 198 | 198 | -0.9351 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 194 | 194 | -1.2957 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 190 | 190 | -2.3927 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3506 | 180 | -0.0945 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 180 | 180 | -0.0945 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 180 | 180 | -0.0945 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 131 | 131 | 0.2871 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 129 | 129 | 0.762 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 112 | 112 | 0.0594 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 80 | 80 | 2.4117 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 75 | 75 | -1.6369 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 65 | 65 | -0.9915 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 59 | 59 | 0.2544 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 49 | 49 | -0.5583 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 48 | 48 | 0.2366 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 42 | 42 | -0.2872 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 42 | 42 | -0.3108 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 42 | 42 | 1.106 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 34 | 34 | 0.2286 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 31 | 31 | 0.694 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 31 | 31 | 2.2636 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 30 | 30 | 1.0301 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 25 | 25 | -0.4121 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 22 | 22 | -0.5488 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 569, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 128274 | 128274 | None | -0.5212 | 0.1867 | `hold_sample` |
| `arm` | `AVG_DOWN` | 104357 | 103740 | None | -0.7947 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 75635 | 75635 | None | -0.5238 | 0.185 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 72421 | 71804 | None | -0.9597 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 31936 | 31936 | None | -0.4236 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 25931 | 24567 | None | 0.6359 | 0.9761 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 25931 | 24567 | None | 0.6359 | 0.9761 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 22045 | 22045 | None | -0.4915 | 0.1911 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 20108 | 20108 | None | 0.481 | 0.9793 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 16969 | 16969 | None | -0.5134 | 0.1877 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 12964 | 12964 | None | -0.338 | 0.1498 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 7660 | 7660 | None | -0.5462 | 0.1832 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 5965 | 5965 | None | -0.5868 | 0.1941 | `hold_sample` |
| `blocker_reason` | `low_broken` | 3001 | 3001 | None | -0.4641 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1526 | 1526 | None | -0.7832 | 0.0872 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1240 | 1240 | None | 3.2454 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1072 | 1072 | None | -2.3477 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 879 | 879 | None | -0.427 | 0.3049 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 868 | 868 | None | -0.91 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 860 | 860 | None | -0.2505 | 0.2209 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 360 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 180 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 360 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `stage` | `exit` | 180 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 360 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 180 | 180 | -0.0945 | -0.1261 | 0.3722 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 356 | 178 | -0.0937 | -0.1249 | 0.3764 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 270 | 135 | -0.0553 | -0.0738 | 0.4 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 226 | 113 | -0.6791 | -0.9055 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 65 | 65 | -0.9915 | -1.322 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 130 | 65 | -0.9915 | -1.322 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 48 | 48 | 0.2366 | 0.3154 | 0.875 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 96 | 48 | 0.2366 | 0.3154 | 0.875 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 90 | 45 | -0.2122 | -0.2829 | 0.2889 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 42 | 42 | -0.2872 | -0.3829 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 84 | 42 | 0.2759 | 0.3679 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 84 | 42 | -0.2872 | -0.3829 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 14 | 14 | 0.8732 | 1.1643 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_pos080_pos150` | 28 | 14 | 0.8732 | 1.1643 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 28 | 14 | 0.8732 | 1.1643 | 1.0 | `candidate_recovery_or_relax` |

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
