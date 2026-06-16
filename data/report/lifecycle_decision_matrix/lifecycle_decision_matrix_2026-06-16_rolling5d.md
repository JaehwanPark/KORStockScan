# Lifecycle Decision Matrix - 2026-06-16

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-16_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `60942`
- source_rows_total: `79295`
- retained_rows: `60942`
- dropped_rows_by_source: `{}`
- joined_rows: `53961`
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
- lifecycle_flow_bucket_count: `321`
- lifecycle_flow_complete_count: `275`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.005`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3322 | 398 | 0.7498 | 0.9177 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1396 | 585 | -0.6621 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1310 | 585 | -1.091 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 52573 | 51538 | -0.4904 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2341 | 855 | -1.0253 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 321, 'complete_flow_count': 275, 'incomplete_flow_count': 54995, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 43251 | 42903 | -0.7332 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 8985 | 8298 | 0.7755 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 274 | 274 | -0.9879 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 71 | 71 | 1.7763 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 64 | 64 | 1.6958 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 45 | 45 | 2.8131 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 18 | 18 | 0.3587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 14 | 14 | -0.9707 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 12 | 12 | -0.8469 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 8 | 8 | -0.87 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 7 | 7 | -0.9457 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 7 | 7 | -1.15 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 6 | 6 | -1.5184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 6 | 6 | -1.3205 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 5 | 5 | -2.3347 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 5 | 5 | -0.7551 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 5 | 5 | 0.8521 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 4 | 4 | -0.6018 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a6f1cf48c2` | 4 | 4 | -3.1019 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:917af9e5d4` | 4 | 4 | -0.9512 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 302, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2608 | 398 | 0.7498 | 0.6717 | 0.4246 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_normal` | 2559 | 320 | 0.5106 | 0.1161 | 0.4062 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2751 | 205 | -0.2426 | -1.2799 | 0.2098 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 180 | 180 | 2.0069 | 3.0013 | 0.6889 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3104 | 180 | 2.0069 | 3.0013 | 0.6889 | `hold_sample` |
| `stale_bucket` | `fresh` | 1674 | 134 | -0.3503 | -1.4121 | 0.1642 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1498 | 134 | -0.3503 | -1.4121 | 0.1642 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 1510 | 117 | -0.2 | -1.18 | 0.1966 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 110 | 110 | -0.1545 | -1.9953 | 0.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 1084 | 88 | -0.3828 | -1.5453 | 0.1477 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 250 | 82 | 1.0876 | 1.8314 | 0.6341 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 778 | 63 | 0.3456 | -0.3441 | 0.3016 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 248 | 55 | 0.8639 | 1.1178 | 0.4727 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 511 | 53 | 0.7384 | 0.8947 | 0.4529 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 682 | 53 | -0.5288 | -1.5611 | 0.151 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 50 | 50 | -0.6594 | -3.004 | 0.0 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 269 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 47 | 47 | 1.47 | 2.1299 | 0.617 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 43 | 43 | -0.4743 | 2.3933 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 160 | 40 | 0.3984 | -0.5582 | 0.3 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 37 | 37 | 1.2586 | 1.5888 | 0.5405 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 34 | 34 | 1.6688 | 2.2708 | 0.853 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 179 | 31 | 1.5118 | 3.3786 | 0.4516 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 372 | 28 | -0.3592 | -1.5304 | 0.1428 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 27 | 27 | 1.3544 | 1.749 | 0.7037 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 675 | 26 | -0.2085 | -1.0711 | 0.1923 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 173 | 15 | -0.1823 | -1.6567 | 0.0667 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1400_close` | 138 | 12 | -0.8942 | -2.6758 | 0.0 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 87, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1367 | 585 | -0.6621 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1256 | 585 | -0.6621 | `keep_collecting` |
| `latency_state` | `simulated` | 1256 | 585 | -0.6621 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1366 | 585 | -0.6621 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1241 | 579 | -0.633 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1137 | 535 | -0.7052 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1025 | 491 | -0.7253 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1000 | 474 | -0.7067 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 704 | 339 | -0.7914 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 613 | 321 | -0.4704 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 703 | 309 | -0.2767 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 703 | 309 | -0.2767 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 565 | 276 | -1.0936 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 522 | 276 | -1.0936 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 522 | 276 | -1.0936 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 658 | 269 | -0.9389 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 471 | 264 | -0.4622 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 576 | 255 | -0.2441 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 551 | 237 | -0.8564 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 387 | 191 | -0.5814 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 319 | 168 | -1.2891 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 368 | 164 | -0.2079 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 245 | 105 | -0.3005 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 231 | 94 | -0.3319 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 188 | 82 | -0.3765 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 91 | 51 | -0.887 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 119 | 50 | -0.201 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 290 | 50 | -0.201 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 119 | 50 | -0.201 | `keep_collecting` |
| `would_limit_fill` | `false` | 258 | 49 | -0.2062 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 111 | 47 | -0.1359 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 64 | 38 | -0.4927 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 90 | 26 | -1.2806 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 18 | 9 | -1.1848 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 15 | 6 | -3.4659 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 6 | 0.2779 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 15 | 6 | -3.4659 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 14 | 4 | -0.6814 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 8 | 4 | -3.3013 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 11 | 4 | -0.9855 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1256 | 585 | -1.091 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1256 | 585 | -1.091 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 500 | 474 | -1.4804 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 692 | 274 | -1.2904 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 502 | 272 | -0.8439 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 230 | 230 | -1.6248 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 207 | 207 | -1.2916 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 62 | 39 | -1.4126 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 37 | 37 | -1.6388 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 35 | 33 | 0.4061 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 27 | 27 | 0.4619 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 21 | 21 | 1.903 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 21 | 21 | 0.2825 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 31 | 16 | -0.4113 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 25 | 14 | 0.3036 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 14 | 14 | 0.5522 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 2.196 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 13 | 13 | 0.3646 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 12 | 12 | 0.6223 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.4437 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | 0.3571 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.0191 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | 0.0811 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.34 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.2814 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 54 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 38 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 671 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 54 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 230 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 418 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 18 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 676 | 676 | -1.355 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 472 | 472 | -1.1808 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 329 | 329 | -0.9126 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 329 | 329 | -0.9126 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 329 | 329 | -0.9126 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 251 | 251 | -1.1144 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 231 | 231 | -1.3828 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 175 | 175 | -1.7021 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 160 | 160 | -0.7991 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 141 | 141 | -1.9888 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 137 | 137 | -0.9607 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 85 | 85 | -1.1677 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 83 | 83 | -0.5084 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 79 | 79 | -1.8792 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 69 | 69 | 0.7666 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 67 | 67 | -0.5522 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 67 | 67 | -1.0705 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 63 | 63 | -1.5256 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 58 | 58 | -2.5518 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1540 | 54 | -0.3523 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 54 | 54 | -0.3523 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 54 | 54 | -0.3523 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 30 | 30 | 0.535 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 28 | 28 | 0.5307 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 28 | 28 | -0.6159 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 26 | 26 | -0.778 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 21 | 21 | 2.1587 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 20 | 20 | -1.8153 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 17 | 17 | 0.3139 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 16 | 16 | -0.3906 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 16 | 16 | 0.066 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 15 | 15 | -0.2775 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 11 | 11 | 0.313 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | 0.0508 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 10 | 10 | 2.3488 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 10 | 10 | 0.507 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 7 | 7 | 1.3008 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.6876 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 0.6503 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -1.1678 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 304, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 51521 | 51521 | None | -0.5487 | 0.1587 | `hold_sample` |
| `arm` | `AVG_DOWN` | 43566 | 43218 | None | -0.7961 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 30343 | 29995 | None | -0.955 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 28450 | 28450 | None | -0.5473 | 0.156 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 13223 | 13223 | None | -0.4355 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 9316 | 9316 | None | -0.5102 | 0.1662 | `hold_sample` |
| `arm` | `PYRAMID` | 9007 | 8320 | None | 0.7393 | 0.9844 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 9007 | 8320 | None | 0.7393 | 0.9844 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 6750 | 6750 | None | -0.5601 | 0.1526 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 6613 | 6613 | None | 0.5034 | 0.987 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 4903 | 4903 | None | -0.3543 | 0.1362 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3698 | 3698 | None | -0.5412 | 0.1674 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3307 | 3307 | None | -0.6537 | 0.163 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1275 | 1275 | None | -0.4792 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 632 | 632 | None | 3.6345 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 474 | 474 | None | -0.93 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 469 | 469 | None | -0.4275 | 0.2836 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 459 | 459 | None | -0.86 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 445 | 445 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 427 | 427 | None | -0.98 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 27, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 108 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 54 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 108 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 54 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 108 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 108 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 54 | 54 | -0.3523 | -0.4698 | 0.2222 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 84 | 42 | -0.5811 | -0.7748 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 76 | 38 | -0.3454 | -0.4605 | 0.2369 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 26 | 26 | -0.778 | -1.0373 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 52 | 26 | -0.778 | -1.0373 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 32 | 16 | -0.3689 | -0.4919 | 0.1875 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 15 | 15 | -0.2775 | -0.37 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 30 | 15 | -0.2775 | -0.37 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 11 | 11 | 0.313 | 0.4173 | 0.9091 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 22 | 11 | 0.313 | 0.4173 | 0.9091 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 20 | 10 | 0.3458 | 0.461 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 2 | 0.96 | 1.28 | 1.0 | `hold_sample` |

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
