# Lifecycle Decision Matrix - 2026-06-16

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-16_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `148966`
- source_rows_total: `224972`
- retained_rows: `148966`
- dropped_rows_by_source: `{}`
- joined_rows: `136447`
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
- lifecycle_flow_bucket_count: `603`
- lifecycle_flow_complete_count: `700`
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
| `entry` | 7023 | 1134 | 0.5294 | 0.9711 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3165 | 2080 | -0.554 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 2960 | 2080 | -0.9443 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 129054 | 127669 | -0.4313 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6764 | 3484 | -0.9678 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 603, 'complete_flow_count': 700, 'incomplete_flow_count': 135245, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 98701 | 98224 | -0.7464 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 28810 | 27902 | 0.6993 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1298 | 1298 | -1.0725 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 236 | 236 | 1.4148 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 194 | 194 | 1.4415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 136 | 136 | 1.4027 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 112 | 112 | -0.2604 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 37 | 37 | -0.9232 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 27 | 27 | -0.8685 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 20 | 20 | -1.0125 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 16 | 16 | -1.1775 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 12 | 12 | -1.9752 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 10 | 10 | -0.4651 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 8 | 8 | -0.9845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 8 | 8 | -1.3383 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 8 | 8 | -0.8364 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 8 | 8 | 0.8893 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 7 | 7 | -1.6888 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 380, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4675 | 1134 | 0.5294 | 0.58 | 0.4515 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 4257 | 800 | 0.465 | 0.1479 | 0.4337 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 566 | 566 | 1.4211 | 2.3286 | 0.6484 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 6455 | 566 | 1.4211 | 2.3286 | 0.6484 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 4699 | 533 | -0.3317 | -1.2142 | 0.2458 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2188 | 397 | -0.3863 | -1.259 | 0.2393 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 2508 | 396 | -0.3862 | -1.2648 | 0.2374 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 2331 | 382 | -0.279 | -1.0865 | 0.2696 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1555 | 319 | 0.6763 | 1.2448 | 0.5956 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 319 | 319 | 0.6763 | 1.2448 | 0.5956 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1566 | 308 | 0.229 | 0.0651 | 0.4448 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 577 | 297 | 0.625 | 1.08 | 0.559 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 268 | 268 | -0.2487 | -1.986 | 0.0 | `hold_no_edge` |
| `score_band` | `score_60_62` | 2378 | 259 | -0.4116 | -1.2421 | 0.2316 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1174 | 211 | 0.4836 | 0.3962 | 0.436 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 499 | 207 | 0.6386 | 1.2804 | 0.5845 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 620 | 159 | 1.0286 | 1.1595 | 0.478 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 1245 | 147 | -0.4474 | -0.8937 | 0.2993 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 465 | 146 | 0.1831 | 1.8087 | 0.5206 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 141 | 141 | -0.623 | 1.937 | 1.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 132 | 132 | -0.4209 | -2.9389 | 0.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 224 | 127 | 0.6404 | 0.8479 | 0.559 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 409 | 111 | 0.1648 | 0.104 | 0.4234 | `hold_no_edge` |
| `time_bucket` | `time_1400_close` | 396 | 50 | -0.8885 | -1.4996 | 0.24 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 93, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3059 | 2080 | -0.554 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2816 | 2080 | -0.554 | `keep_collecting` |
| `latency_state` | `simulated` | 2816 | 2080 | -0.554 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3056 | 2080 | -0.554 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2776 | 2050 | -0.5363 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2582 | 1921 | -0.5802 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2295 | 1704 | -0.5733 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2272 | 1673 | -0.605 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1760 | 1327 | -0.6969 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1608 | 1200 | -0.5941 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1547 | 1191 | -0.6372 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1558 | 1184 | -0.6952 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1460 | 1184 | -0.6952 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1460 | 1184 | -0.6952 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1324 | 896 | -0.3673 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1324 | 896 | -0.3673 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1079 | 769 | -0.3796 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1070 | 721 | -0.3443 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 923 | 712 | -0.5656 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 844 | 674 | -0.7572 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 809 | 587 | -0.3184 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 716 | 490 | -0.3309 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 527 | 377 | -0.2316 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 521 | 376 | -0.4664 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 286 | 238 | -0.5959 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 321 | 210 | -0.4271 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 198 | 171 | -0.3117 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 234 | 159 | -0.2374 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 615 | 159 | -0.2374 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 234 | 159 | -0.2374 | `keep_collecting` |
| `would_limit_fill` | `false` | 582 | 158 | -0.2393 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 212 | 142 | -0.0763 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 187 | 118 | -0.8589 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 46 | 39 | -2.0609 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 40 | 30 | -1.7602 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 39 | 30 | -0.7669 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 40 | 30 | -1.7602 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 20 | 16 | -2.6943 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 21 | 16 | -1.6853 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 20 | 15 | 0.1872 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2816 | 2080 | -0.9443 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2816 | 2080 | -0.9443 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1603 | 1547 | -1.4439 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1799 | 1335 | -1.0586 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1007 | 1007 | -1.525 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 853 | 612 | -0.6693 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 425 | 425 | -1.2596 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 186 | 174 | 0.2062 | `hold_no_edge` |
| `holding_action` | `BUY` | 164 | 133 | -1.0624 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 138 | 132 | 0.5302 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 115 | 115 | -1.4151 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 148 | 113 | 0.0518 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 108 | 108 | 0.0946 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 84 | 84 | 0.0196 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 85 | 82 | 2.0691 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 76 | 76 | 0.4001 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 64 | 64 | 0.375 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 46 | 46 | 0.6881 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 43 | 43 | 1.9978 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 34 | 34 | 2.1524 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 64 | 32 | -0.3678 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 28 | 28 | 0.105 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 17 | 17 | -0.3359 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 15 | 15 | -0.4039 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 2.1165 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 144 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 45 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 99 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 736 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 144 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 241 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 464 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 40 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 23 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2629 | 2629 | -1.3368 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1809 | 1809 | -1.0015 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1531 | 1531 | -1.0047 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1531 | 1531 | -1.0047 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1531 | 1531 | -1.0047 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1180 | 1180 | -1.2061 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 778 | 778 | -1.2942 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 695 | 695 | -1.5105 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 644 | 644 | -0.5448 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 536 | 536 | -1.8433 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 470 | 470 | -0.8745 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 405 | 405 | 0.5395 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 348 | 348 | -0.5149 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 311 | 311 | -0.5403 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 287 | 287 | -1.695 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 252 | 252 | -1.1987 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 239 | 239 | -0.9136 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 232 | 232 | -1.3342 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 222 | 222 | -2.4093 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 156 | 156 | 0.2448 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3424 | 144 | -0.1522 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 144 | 144 | -0.1522 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 144 | 144 | -0.1522 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 142 | 142 | 0.0936 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 127 | 127 | 0.6425 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 84 | 84 | -0.4953 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 82 | 82 | 2.3012 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 82 | 82 | -1.7515 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 56 | 56 | -1.0067 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 53 | 53 | -0.0012 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 52 | 52 | -0.4039 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 45 | 45 | 0.3051 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 44 | 44 | 1.0794 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -0.4419 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 39 | 39 | 0.7604 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 37 | 37 | 2.295 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 35 | 35 | 0.2848 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 32 | 32 | -0.2942 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 29 | 29 | -0.5257 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 29 | 29 | 0.4014 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 483, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 127647 | 127647 | None | -0.5031 | 0.2151 | `hold_sample` |
| `arm` | `AVG_DOWN` | 100123 | 99646 | None | -0.8239 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 70855 | 70378 | None | -0.9897 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 68936 | 68936 | None | -0.5104 | 0.2101 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 29268 | 29268 | None | -0.4251 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 28931 | 28023 | None | 0.6381 | 0.9806 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 28931 | 28023 | None | 0.6381 | 0.9806 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 24206 | 24206 | None | 0.5337 | 0.9824 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 22779 | 22779 | None | -0.4449 | 0.2386 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 19714 | 19714 | None | -0.5131 | 0.2138 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 10007 | 10007 | None | -0.3172 | 0.1822 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 8482 | 8482 | None | -0.5155 | 0.2098 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 7736 | 7736 | None | -0.5711 | 0.2005 | `hold_sample` |
| `blocker_reason` | `low_broken` | 2841 | 2841 | None | -0.4634 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1741 | 1741 | None | -0.8449 | 0.0827 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1236 | 1236 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1198 | 1198 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1175 | 1175 | None | -2.3682 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1153 | 1153 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 1029 | 1029 | None | -0.82 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 288 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 144 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 288 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 144 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 288 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 288 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 144 | 144 | -0.1522 | -0.203 | 0.3611 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 198 | 99 | -0.1432 | -0.1909 | 0.3738 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 184 | 92 | -0.7168 | -0.9558 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 56 | 56 | -1.0067 | -1.3423 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 112 | 56 | -1.0067 | -1.3423 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 90 | 45 | -0.1721 | -0.2296 | 0.3333 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 35 | 35 | 0.2848 | 0.3797 | 0.8857 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 70 | 35 | 0.2848 | 0.3797 | 0.8857 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 32 | 32 | -0.2942 | -0.3922 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 64 | 32 | -0.2942 | -0.3922 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 62 | 31 | 0.3266 | 0.4355 | 1.0 | `hold_sample` |
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
