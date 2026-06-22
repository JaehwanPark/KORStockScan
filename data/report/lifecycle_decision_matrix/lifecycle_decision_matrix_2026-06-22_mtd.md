# Lifecycle Decision Matrix - 2026-06-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-22_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `217866`
- source_rows_total: `323710`
- retained_rows: `217866`
- dropped_rows_by_source: `{}`
- joined_rows: `198167`
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
- lifecycle_flow_bucket_count: `895`
- lifecycle_flow_complete_count: `1113`
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
| `entry` | 12010 | 1654 | 0.7144 | 0.9606 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4270 | 2823 | -0.4945 | 0.998 | `pass` | `NO_CHANGE` | False |
| `holding` | 4023 | 2823 | -0.9168 | 0.9977 | `pass` | `EXIT` | False |
| `scale_in` | 187998 | 185838 | -0.4323 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 9565 | 5029 | -0.934 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 895, 'complete_flow_count': 1113, 'incomplete_flow_count': 197275, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 145631 | 144970 | -0.7274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 40218 | 38719 | 0.6924 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1768 | 1768 | -1.0511 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 376 | 376 | 1.5574 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 298 | 298 | 1.6041 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 205 | 205 | 1.5507 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 150 | 150 | -0.2149 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 62 | 62 | -0.9337 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 41 | 41 | -0.7588 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 36 | 36 | -0.8619 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 20 | 20 | -2.0219 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 19 | 19 | -1.23 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 15 | 15 | -0.5468 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 15 | 15 | -0.9207 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 13 | 13 | -0.7433 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 12 | 12 | -1.0708 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 12 | 12 | -0.2525 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 12 | 12 | -0.2913 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 522, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 8189 | 1645 | 0.7149 | 0.7857 | 0.4693 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 7924 | 1242 | 0.5833 | 0.2589 | 0.4476 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 886 | 886 | 1.5674 | 2.5016 | 0.658 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 11242 | 886 | 1.5674 | 2.5016 | 0.658 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 8596 | 702 | -0.2558 | -1.2501 | 0.2436 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2500 | 639 | 1.2522 | 2.0274 | 0.6354 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 639 | 639 | 1.2522 | 2.0274 | 0.6354 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 5672 | 601 | 0.0087 | -0.7418 | 0.2978 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 5167 | 597 | -0.2622 | -1.2646 | 0.2378 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1219 | 581 | 1.1008 | 1.6931 | 0.5955 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5305 | 569 | -0.278 | -1.2161 | 0.2443 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2704 | 478 | 0.6681 | 0.735 | 0.4979 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1075 | 396 | 1.0028 | 1.597 | 0.5859 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 363 | 363 | -0.1976 | -1.9811 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 5204 | 359 | -0.2873 | -1.3485 | 0.22 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1961 | 318 | 0.5453 | 0.4454 | 0.4371 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 469 | 241 | 1.155 | 1.6919 | 0.5975 | `hold_sample` |
| `score_band` | `score_63_65` | 840 | 199 | 0.6922 | 0.9437 | 0.4975 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 1079 | 194 | 1.0711 | 1.4963 | 0.5206 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 190 | 190 | -0.2177 | -2.9532 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 188 | 188 | -0.5327 | 2.0109 | 1.0 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 1519 | 181 | -0.0058 | -0.3004 | 0.337 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 110 | 110 | 1.0647 | 1.4054 | 0.6364 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 178, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4136 | 2823 | -0.4945 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3766 | 2823 | -0.4945 | `keep_collecting` |
| `latency_state` | `simulated` | 3766 | 2823 | -0.4945 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4119 | 2823 | -0.4945 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3721 | 2789 | -0.4802 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3480 | 2626 | -0.5123 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3149 | 2361 | -0.4982 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3054 | 2274 | -0.532 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2231 | 1680 | -0.5208 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2107 | 1611 | -0.6429 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1964 | 1611 | -0.6429 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1964 | 1611 | -0.6429 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1969 | 1500 | -0.6692 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1734 | 1344 | -0.6158 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1813 | 1338 | -0.3491 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1768 | 1210 | -0.2972 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1768 | 1210 | -0.2972 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1491 | 1114 | -0.3036 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1461 | 996 | -0.2671 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1180 | 888 | -0.541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 788 | 581 | -0.234 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 692 | 515 | -0.2516 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 746 | 462 | -0.4756 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 245 | 201 | -0.478 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 751 | 199 | -0.2569 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 286 | 197 | -0.2568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 286 | 197 | -0.2568 | `keep_collecting` |
| `would_limit_fill` | `false` | 789 | 196 | -0.2584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 243 | 152 | 0.0614 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 3765 | 2823 | -0.9168 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3765 | 2823 | -0.9168 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2190 | 2095 | -1.4284 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2036 | 1526 | -1.0192 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1142 | 1142 | -1.4983 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1528 | 1131 | -0.7557 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 811 | 811 | -1.3321 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 245 | 224 | 0.2419 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 197 | 185 | 0.6417 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 201 | 166 | -1.0731 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 206 | 148 | 0.0676 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 142 | 142 | -1.416 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 121 | 114 | 2.1248 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 98 | 98 | 0.3921 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 92 | 92 | 0.4714 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 82 | 82 | 0.8137 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 122 | 57 | -0.3645 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 55 | 55 | 2.3269 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 52 | 52 | 2.012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 51 | 51 | 0.1148 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 34 | 34 | -0.3917 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 23 | 23 | -0.3244 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 258 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 69 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 189 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 942 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 258 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 397 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 510 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 68 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 42 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3724 | 3724 | -1.3291 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2658 | 2658 | -0.9885 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2113 | 2113 | -0.9686 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2113 | 2113 | -0.9686 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2113 | 2113 | -0.9686 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1571 | 1571 | -1.2036 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1177 | 1177 | -1.2763 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1010 | 1010 | -1.4694 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 948 | 948 | -0.5302 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 798 | 798 | -1.7825 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 700 | 700 | -0.9152 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 589 | 589 | 0.5694 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 542 | 542 | -0.5034 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 473 | 473 | -0.534 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 411 | 411 | -1.6969 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 407 | 407 | -1.1831 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 359 | 359 | -0.9006 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 352 | 352 | -1.2475 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 318 | 318 | -2.423 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 4794 | 258 | -0.09 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 258 | 258 | -0.09 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 258 | 258 | -0.09 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 237 | 237 | 0.2699 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 205 | 205 | 0.0832 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 196 | 196 | 0.7275 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 128 | 128 | -1.6627 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 125 | 125 | 2.4117 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 95 | 95 | -0.9613 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 85 | 85 | -0.3501 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 82 | 82 | 0.1391 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 68 | 68 | 1.1124 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 64 | 64 | -0.2889 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 60 | 60 | 0.3145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 59 | 59 | 0.2249 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 56 | 56 | 0.7905 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 50 | 50 | 2.4099 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 45 | 45 | 1.0441 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 42 | 42 | -0.4983 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -0.4387 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 833, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 185799 | 185799 | None | -0.5001 | 0.2045 | `hold_sample` |
| `arm` | `AVG_DOWN` | 147601 | 146940 | None | -0.7993 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 106010 | 106010 | None | -0.5039 | 0.201 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 103014 | 102353 | None | -0.9628 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 44587 | 44587 | None | -0.424 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 40397 | 38898 | None | 0.6316 | 0.9778 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 40397 | 38898 | None | 0.6316 | 0.9778 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 34340 | 34340 | None | -0.4654 | 0.2166 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 32759 | 32759 | None | 0.5165 | 0.9816 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 24118 | 24118 | None | -0.5107 | 0.2096 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 18480 | 18480 | None | -0.3262 | 0.1617 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 11885 | 11885 | None | -0.5037 | 0.1953 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9446 | 9446 | None | -0.5522 | 0.1988 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4104 | 4104 | None | -0.4602 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2467 | 2467 | None | -0.8291 | 0.088 | `hold_sample` |
| `blocker_reason` | `ok` | 1614 | 1614 | None | -2.38 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1464 | 1464 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1448 | 1448 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1370 | 1370 | None | 3.2357 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1315 | 1315 | None | -1.1 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 516 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 258 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 516 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 258 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 516 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 258 | 258 | -0.09 | -0.12 | 0.3488 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 512 | 256 | -0.0894 | -0.1192 | 0.3516 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 378 | 189 | -0.0278 | -0.0371 | 0.3757 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 336 | 168 | -0.6563 | -0.875 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 95 | 95 | -0.9613 | -1.2818 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 190 | 95 | -0.9613 | -1.2818 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 138 | 69 | -0.2604 | -0.3473 | 0.2754 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 65 | 65 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 130 | 65 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 58 | 58 | 0.23 | 0.3067 | 0.8621 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 116 | 58 | 0.23 | 0.3067 | 0.8621 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 100 | 50 | 0.2741 | 0.3654 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 21 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 42 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 42 | 21 | 0.8525 | 1.1367 | 1.0 | `hold_sample` |

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
