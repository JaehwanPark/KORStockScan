# Lifecycle Decision Matrix - 2026-06-12

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-12_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `107303`
- source_rows_total: `165464`
- retained_rows: `107303`
- dropped_rows_by_source: `{}`
- joined_rows: `98573`
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
- lifecycle_flow_bucket_count: `500`
- lifecycle_flow_complete_count: `519`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4606 | 882 | 0.4317 | 1.0 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 2554 | 1749 | -0.5821 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 2390 | 1749 | -0.9612 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 92193 | 91339 | -0.4013 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5560 | 2854 | -0.9871 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 500, 'complete_flow_count': 519, 'incomplete_flow_count': 97122, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 68119 | 67808 | -0.7544 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 22868 | 22325 | 0.6948 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1024 | 1024 | -1.0951 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 177 | 177 | 1.1708 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 155 | 155 | 1.2592 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 129 | 129 | 1.2821 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 94 | 94 | -0.3789 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 23 | 23 | -0.8943 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 19 | 19 | -0.8679 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 13 | 13 | -1.0485 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -1.1989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 7 | 7 | -1.7184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 6 | 6 | -1.9202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 6 | 6 | -1.7784 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 6 | 6 | -0.374 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a2a88f9390` | 6 | 6 | -2.1579 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6564dad233` | 5 | 5 | -1.1155 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 5 | 5 | -0.9619 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 334, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2879 | 881 | 0.4276 | 0.6118 | 0.4631 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2448 | 594 | 0.4962 | 0.3705 | 0.4545 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 462 | 462 | 1.2377 | 2.2712 | 0.6494 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 4186 | 462 | 1.2377 | 2.2712 | 0.6494 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 2750 | 398 | -0.4448 | -1.2617 | 0.2437 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1362 | 348 | 0.7913 | 1.6338 | 0.6264 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 348 | 348 | 0.7913 | 1.6338 | 0.6264 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1520 | 342 | -0.2916 | -0.9506 | 0.3012 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1336 | 333 | -0.4696 | -1.2853 | 0.2462 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 1569 | 332 | -0.4698 | -1.2923 | 0.244 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1153 | 328 | 0.4195 | 0.7541 | 0.5061 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 475 | 302 | 0.7739 | 1.5406 | 0.5894 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1698 | 218 | -0.498 | -1.226 | 0.2385 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 191 | 191 | -0.3799 | -2.0005 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 871 | 179 | 0.4965 | 0.3576 | 0.4525 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 349 | 142 | 0.7909 | 1.2861 | 0.5493 | `hold_no_edge` |
| `score_band` | `score_66_69` | 195 | 134 | 0.7651 | 1.5045 | 0.6194 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 443 | 133 | 0.7862 | 0.7436 | 0.4511 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 365 | 132 | -0.1129 | 1.3982 | 0.5227 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 255 | 131 | 0.1757 | 0.6773 | 0.5343 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 830 | 125 | -0.5152 | -0.7881 | 0.328 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 106 | 106 | -0.3924 | -2.9112 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 106 | 106 | -0.7481 | 1.8182 | 1.0 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1400_close` | 323 | 49 | -0.8788 | -1.4749 | 0.2449 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 85, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 3226 | 2415 | -0.5263 | `keep_collecting` |
| `actual_order_submitted` | `false` | 3013 | 1876 | -0.5576 | `keep_collecting` |
| `actual_order_submitted` | `true` | 2553 | 1750 | -0.5817 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2281 | 1749 | -0.5821 | `keep_collecting` |
| `latency_state` | `simulated` | 2281 | 1749 | -0.5821 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2096 | 1621 | -0.6108 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1835 | 1420 | -0.609 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1828 | 1401 | -0.648 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1616 | 1243 | -0.6882 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1432 | 1115 | -0.6207 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1308 | 1083 | -0.7064 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1343 | 1055 | -0.6803 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1270 | 1055 | -0.6803 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1307 | 1018 | -0.6278 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 983 | 694 | -0.4326 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 728 | 599 | -0.734 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 745 | 597 | -0.595 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 780 | 552 | -0.425 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 686 | 523 | -0.4346 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 537 | 386 | -0.4318 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 467 | 371 | -0.3552 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 446 | 329 | -0.4655 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 435 | 320 | -0.1963 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 244 | 206 | -0.6137 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 177 | 155 | -0.2635 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 221 | 152 | -0.4668 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 185 | 128 | -0.2187 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 486 | 128 | -0.2187 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 185 | 128 | -0.2187 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 164 | 112 | -0.0363 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 161 | 110 | -0.8969 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 45 | 39 | -2.0609 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 38 | 28 | -1.6902 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 33 | 26 | -0.7857 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 20 | 15 | -1.5985 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 18 | 14 | -2.6878 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 13 | -0.3691 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 10 | 0.1187 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 10 | -0.7459 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 9 | -2.502 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2281 | 1749 | -0.9612 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2281 | 1749 | -0.9612 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1335 | 1293 | -1.4766 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1649 | 1248 | -1.0565 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 939 | 939 | -1.5279 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 481 | 378 | -0.6002 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 248 | 248 | -1.2967 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 163 | 151 | 0.1969 | `hold_no_edge` |
| `holding_action` | `BUY` | 151 | 123 | -1.1038 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 121 | 115 | 0.5122 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 106 | 106 | -1.4426 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 105 | 105 | 0.0855 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 126 | 101 | 0.0347 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 78 | 78 | -0.0027 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 72 | 72 | 0.3972 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 71 | 68 | 2.116 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 44 | 44 | 0.4341 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 39 | 39 | 2.1611 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 33 | 33 | 0.6782 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 25 | 25 | 2.1321 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 22 | 22 | 0.1115 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 42 | 21 | -0.3785 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 15 | 15 | -0.3601 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.4247 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.5753 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 109 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 42 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 67 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 532 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 109 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 103 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 401 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 70, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2148 | 2148 | -1.3677 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1543 | 1543 | -1.0157 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 929 | 929 | -1.2309 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 640 | 640 | -1.3305 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 602 | 602 | -1.5172 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 558 | 558 | -0.5569 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 468 | 468 | -1.8377 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 383 | 383 | -0.8961 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 356 | 356 | 0.499 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 270 | 270 | -0.516 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 248 | 248 | -1.7159 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 244 | 244 | -0.537 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 218 | 218 | -0.1097 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 206 | 206 | -1.3438 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 196 | 196 | -0.9245 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 196 | 196 | -1.2487 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 191 | 191 | -2.3989 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 133 | 133 | 0.2022 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 127 | 127 | 0.0764 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 2815 | 109 | -0.1097 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 109 | 109 | 0.625 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 74 | 74 | -0.5154 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 71 | 71 | -1.761 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 67 | 67 | 2.3154 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 43 | 43 | -0.4912 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 43 | 43 | -0.0626 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 42 | 42 | -1.1027 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 40 | 40 | 1.0462 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 37 | 37 | 0.7416 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 37 | 37 | 0.2344 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 32 | 32 | -0.459 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 29 | 29 | -0.5257 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 29 | 29 | 0.4014 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 29 | 29 | 2.2194 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 25 | 25 | 0.2802 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 24 | 24 | 1.2595 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 24 | 24 | 0.0245 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 400, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 118364 | 117742 | -0.8269 | -0.9132 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 91328 | 91328 | -0.4014 | -0.4803 | 0.2406 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 46752 | 46752 | -0.4029 | -0.488 | 0.2381 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 45934 | 44848 | 0.6939 | 0.6284 | 0.9803 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 20088 | 20088 | -0.3519 | -0.4168 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 19858 | 19858 | 0.6134 | 0.5398 | 0.9819 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 16627 | 16627 | -0.3178 | -0.395 | 0.2734 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 16333 | 16333 | -0.4418 | -0.5014 | 0.2296 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 6292 | 6292 | -0.4482 | -0.5229 | 0.2215 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 5472 | 5472 | -0.2638 | -0.2854 | 0.221 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 5324 | 5324 | -0.471 | -0.5635 | 0.2162 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 2096 | 2096 | -0.4302 | -0.455 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1370 | 1370 | -0.8795 | -0.8791 | 0.0883 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 992 | 992 | -1.9469 | -2.3969 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 950 | 950 | -1.0572 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 942 | 942 | -0.8559 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 841 | 841 | -1.0131 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 821 | 821 | -0.7176 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 791 | 791 | -0.6742 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 790 | 790 | -0.9223 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 786 | 786 | -1.2535 | -1.37 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 695 | 695 | -1.2679 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 619 | 619 | -0.8639 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 613 | 613 | -0.7898 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 608 | 608 | -0.8075 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 573 | 573 | -1.0924 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 558 | 558 | -0.9648 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 554 | 554 | -1.0207 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 552 | 552 | -0.9331 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 526 | 526 | -0.8241 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 505 | 505 | -0.9383 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 500 | 500 | -0.6564 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 495 | 495 | -0.6449 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 485 | 485 | -0.7502 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 476 | 476 | 3.2015 | 3.3834 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 471 | 471 | -0.8204 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 458 | 458 | -0.2344 | -0.2929 | 0.3101 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 443 | 443 | 2.9305 | 3.004 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 437 | 437 | -0.8518 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 434 | 434 | -0.7266 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 327 | 218 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 218 | 109 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 109 | 109 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 218 | 109 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 218 | 109 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 109 | 109 | -0.1097 | -0.1462 | 0.3945 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 134 | 67 | -0.0817 | -0.109 | 0.4179 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 132 | 66 | -0.8031 | -1.0708 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 42 | 42 | -1.1027 | -1.4703 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 84 | 42 | -0.1543 | -0.2057 | 0.3572 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 84 | 42 | -1.1027 | -1.4703 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 25 | 25 | 0.2802 | 0.3736 | 0.88 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 50 | 25 | 0.2802 | 0.3736 | 0.88 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 44 | 22 | 0.3249 | 0.4332 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 21 | 21 | -0.3118 | -0.4157 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 42 | 21 | -0.3118 | -0.4157 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 12 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 24 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 24 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 6 | 6 | 1.4287 | 1.905 | 1.0 | `hold_sample` |

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
