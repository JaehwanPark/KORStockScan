# Lifecycle Decision Matrix - 2026-06-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-15_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `126781`
- source_rows_total: `197887`
- retained_rows: `126781`
- dropped_rows_by_source: `{}`
- joined_rows: `116181`
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
- lifecycle_flow_bucket_count: `539`
- lifecycle_flow_complete_count: `598`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
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
| `entry` | 5810 | 917 | 0.3534 | 0.9643 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 2872 | 1890 | -0.5553 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 2682 | 1890 | -0.9402 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 109222 | 108303 | -0.433 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6195 | 3181 | -0.9676 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 539, 'complete_flow_count': 598, 'incomplete_flow_count': 114775, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 82990 | 82640 | -0.7545 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 24820 | 24251 | 0.6854 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1210 | 1210 | -1.0735 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 192 | 192 | 1.378 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 146 | 146 | 1.1981 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 98 | 98 | -0.2538 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 95 | 95 | 0.7649 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 29 | 29 | -0.8889 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 21 | 21 | -0.8534 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 17 | 17 | -0.9947 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 12 | 12 | -1.145 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 9 | 9 | -1.8072 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 8 | 8 | -0.9845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 7 | 7 | -1.6888 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 7 | 7 | -0.3734 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 6 | 6 | -1.9202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b705884db4` | 6 | 6 | -0.4108 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 6 | 6 | -0.8388 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 346, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3745 | 917 | 0.3534 | 0.3285 | 0.4297 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 3324 | 628 | 0.3936 | -0.0045 | 0.4124 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 3739 | 459 | -0.3731 | -1.2353 | 0.2396 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 433 | 433 | 1.1828 | 2.0274 | 0.6282 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 5326 | 433 | 1.1828 | 2.0274 | 0.6282 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2188 | 397 | -0.3863 | -1.259 | 0.2393 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 2508 | 396 | -0.3862 | -1.2648 | 0.2374 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 2331 | 382 | -0.279 | -1.0865 | 0.2696 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1555 | 319 | 0.6763 | 1.2448 | 0.5956 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 319 | 319 | 0.6763 | 1.2448 | 0.5956 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1566 | 308 | 0.229 | 0.0651 | 0.4448 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 577 | 297 | 0.625 | 1.08 | 0.559 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 2378 | 259 | -0.4116 | -1.2421 | 0.2316 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 226 | 226 | -0.2929 | -1.9859 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1174 | 211 | 0.4836 | 0.3962 | 0.436 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 347 | 150 | 0.5179 | 1.1227 | 0.5733 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 1245 | 147 | -0.4474 | -0.8937 | 0.2993 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 508 | 135 | 0.6416 | 0.6507 | 0.4445 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 400 | 131 | -0.2135 | 1.2352 | 0.5038 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 224 | 127 | 0.6404 | 0.8479 | 0.559 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 118 | 118 | -0.694 | 1.8537 | 1.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 116 | 116 | -0.39 | -2.8946 | 0.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 409 | 111 | 0.1648 | 0.104 | 0.4234 | `hold_no_edge` |
| `time_bucket` | `time_1400_close` | 396 | 50 | -0.8885 | -1.4996 | 0.24 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 91, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 2769 | 1890 | -0.5553 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2558 | 1890 | -0.5553 | `keep_collecting` |
| `latency_state` | `simulated` | 2558 | 1890 | -0.5553 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 2767 | 1890 | -0.5553 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2520 | 1862 | -0.5382 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2345 | 1748 | -0.5851 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2074 | 1544 | -0.5794 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2064 | 1523 | -0.6172 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1688 | 1274 | -0.6945 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1481 | 1140 | -0.6237 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1445 | 1103 | -0.6752 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1358 | 1103 | -0.6752 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1358 | 1103 | -0.6752 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1459 | 1094 | -0.5996 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1168 | 787 | -0.3872 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1168 | 787 | -0.3872 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 838 | 648 | -0.5725 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 896 | 635 | -0.3758 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 937 | 631 | -0.3809 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 785 | 629 | -0.7339 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 644 | 467 | -0.2894 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 630 | 432 | -0.3742 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 484 | 346 | -0.4477 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 479 | 339 | -0.1836 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 265 | 220 | -0.5814 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 281 | 183 | -0.4462 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 182 | 158 | -0.2774 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 213 | 142 | -0.1884 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 559 | 142 | -0.1884 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 213 | 142 | -0.1884 | `keep_collecting` |
| `would_limit_fill` | `false` | 526 | 141 | -0.1901 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 191 | 125 | 0.0013 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 179 | 114 | -0.8761 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 46 | 39 | -2.0609 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 38 | 28 | -1.6902 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 38 | 28 | -1.6902 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 35 | 27 | -0.7779 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 21 | 16 | -1.6853 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 18 | 14 | -2.6878 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 18 | 13 | -0.3691 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2558 | 1890 | -0.9402 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2558 | 1890 | -0.9402 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1447 | 1399 | -1.4449 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1722 | 1277 | -1.0544 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 960 | 960 | -1.5243 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 684 | 490 | -0.6015 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 333 | 333 | -1.2168 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 172 | 160 | 0.2069 | `hold_no_edge` |
| `holding_action` | `BUY` | 152 | 123 | -1.1038 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 129 | 123 | 0.5134 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 134 | 106 | 0.0261 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 106 | 106 | -1.4426 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 106 | 106 | 0.0887 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 80 | 80 | -0.0015 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 78 | 75 | 2.0791 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 75 | 75 | 0.3756 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 52 | 52 | 0.4242 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 40 | 40 | 2.1245 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 38 | 38 | 0.712 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 31 | 31 | 2.0854 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 54 | 27 | -0.3889 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 25 | 25 | 0.0648 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 16 | 16 | -0.3494 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.4462 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.5753 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 124 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 45 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 79 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 668 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 124 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 29 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 194 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 445 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 32 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 16 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2398 | 2398 | -1.3359 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1650 | 1650 | -0.9956 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1407 | 1407 | -1.0075 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1407 | 1407 | -1.0075 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1407 | 1407 | -1.0075 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1087 | 1087 | -1.2067 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 698 | 698 | -1.3027 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 634 | 634 | -1.4985 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 594 | 594 | -0.5405 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 489 | 489 | -1.8254 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 422 | 422 | -0.8805 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 376 | 376 | 0.5149 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 318 | 318 | -0.5214 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 286 | 286 | -0.5441 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 262 | 262 | -1.7032 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 222 | 222 | -1.2154 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 216 | 216 | -1.3316 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 214 | 214 | -0.9028 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 200 | 200 | -2.3868 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 141 | 141 | 0.2266 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 131 | 131 | 0.0729 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 3138 | 124 | -0.1421 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 124 | 124 | -0.1421 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 124 | 124 | -0.1421 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 118 | 118 | 0.6336 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 81 | 81 | -0.5034 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 75 | 75 | 2.3327 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 73 | 73 | -1.7486 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 48 | 48 | -1.0564 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 48 | 48 | -0.0164 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 46 | 46 | -0.4477 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 41 | 41 | 1.0356 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 39 | 39 | 0.2561 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 38 | 38 | -0.4453 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 38 | 38 | 0.7542 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 33 | 33 | 2.2357 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 29 | 29 | -0.5257 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 29 | 29 | 0.4014 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 28 | 28 | 0.2732 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 27 | 27 | -0.3134 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 447, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 108291 | 108291 | None | -0.5075 | 0.2203 | `hold_sample` |
| `arm` | `AVG_DOWN` | 84298 | 83948 | None | -0.8346 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 60048 | 59698 | None | -1.0017 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 56113 | 56113 | None | -0.5172 | 0.2157 | `hold_sample` |
| `arm` | `PYRAMID` | 24924 | 24355 | None | 0.6204 | 0.98 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 24924 | 24355 | None | 0.6204 | 0.98 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 24250 | 24250 | None | -0.4231 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 21450 | 21450 | None | 0.5375 | 0.9818 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 19606 | 19606 | None | -0.4369 | 0.2486 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 18218 | 18218 | None | -0.5187 | 0.2163 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 7426 | 7426 | None | -0.5285 | 0.2064 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 7412 | 7412 | None | -0.3119 | 0.1913 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 6928 | 6928 | None | -0.5765 | 0.2034 | `hold_sample` |
| `blocker_reason` | `low_broken` | 2491 | 2491 | None | -0.4642 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1601 | 1601 | None | -0.8559 | 0.0812 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1135 | 1135 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1058 | 1058 | None | -2.3785 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1026 | 1026 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 987 | 987 | None | -0.82 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 965 | 965 | None | -1.1 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 248 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 124 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 248 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 124 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 248 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 248 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 124 | 124 | -0.1421 | -0.1894 | 0.3629 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 158 | 79 | -0.1249 | -0.1666 | 0.3798 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 158 | 79 | -0.751 | -1.0013 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 48 | 48 | -1.0564 | -1.4086 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 96 | 48 | -1.0564 | -1.4086 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 90 | 45 | -0.1721 | -0.2296 | 0.3333 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 28 | 28 | 0.2732 | 0.3643 | 0.8571 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 56 | 28 | 0.2732 | 0.3643 | 0.8571 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 27 | 27 | -0.3134 | -0.4178 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 54 | 27 | -0.3134 | -0.4178 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 48 | 24 | 0.3253 | 0.4337 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 12 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 24 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 24 | 12 | 0.8487 | 1.1317 | 1.0 | `hold_sample` |

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
