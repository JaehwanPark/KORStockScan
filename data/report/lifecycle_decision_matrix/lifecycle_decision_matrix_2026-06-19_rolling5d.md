# Lifecycle Decision Matrix - 2026-06-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-19_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `89957`
- source_rows_total: `125133`
- retained_rows: `89957`
- dropped_rows_by_source: `{}`
- joined_rows: `81250`
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
- lifecycle_flow_bucket_count: `465`
- lifecycle_flow_complete_count: `469`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0057`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 6051 | 678 | 1.1577 | 0.9795 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1315 | 799 | -0.3306 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1222 | 799 | -0.8119 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 78656 | 77531 | -0.454 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2713 | 1443 | -0.8474 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 465, 'complete_flow_count': 469, 'incomplete_flow_count': 81839, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 63230 | 62926 | -0.7026 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 14743 | 13922 | 0.6823 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 552 | 552 | -0.9808 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 164 | 164 | 1.8581 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 156 | 156 | 1.9873 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 79 | 79 | 2.2336 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 42 | 42 | -0.107 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 27 | 27 | -0.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 19 | 19 | -0.7452 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 13 | 13 | -2.1853 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 10 | 10 | -0.9068 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 10 | 10 | -0.911 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 9 | 9 | -1.3358 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.4858 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 8 | 8 | -0.2747 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -1.2062 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 7 | 7 | -2.5363 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 7 | 7 | -0.3562 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.436 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 387, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4497 | 673 | 1.1519 | 1.2927 | 0.5037 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 4672 | 572 | 0.7976 | 0.5679 | 0.4738 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 404 | 404 | 1.9824 | 2.9917 | 0.6856 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 5777 | 404 | 1.9824 | 2.9917 | 0.6856 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 853 | 271 | 1.8773 | 2.8358 | 0.6716 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 271 | 271 | 1.8773 | 2.8358 | 0.6716 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 620 | 248 | 1.6643 | 2.3792 | 0.621 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 4805 | 239 | -0.006 | -1.211 | 0.2385 | `hold_no_edge` |
| `score_band` | `score_70p` | 670 | 214 | 1.3764 | 2.0549 | 0.6121 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 3331 | 201 | 0.4197 | -0.3316 | 0.3234 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3106 | 190 | -0.0005 | -1.2573 | 0.2158 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 3137 | 178 | -0.0145 | -1.2076 | 0.2247 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1121 | 148 | 1.4401 | 1.9126 | 0.5743 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 134 | 134 | 0.0203 | -1.9468 | 0.0 | `hold_no_edge` |
| `score_band` | `score_66_69` | 268 | 119 | 1.7272 | 2.4956 | 0.6134 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 2802 | 105 | 0.1074 | -1.5628 | 0.181 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 624 | 97 | 1.1064 | 0.9734 | 0.433 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 90 | 90 | 1.576 | 2.1297 | 0.6444 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 90 | 90 | 1.6447 | 2.4625 | 0.7667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 67 | 67 | -0.0819 | -2.9816 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 63 | 63 | -0.269 | 2.2929 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 308 | 60 | 0.5293 | -1.3437 | 0.2333 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 50 | 50 | 1.3352 | 1.6854 | 0.64 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 694 | 40 | -0.1473 | -0.7488 | 0.325 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 671 | 30 | -0.1048 | -1.6057 | 0.1333 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 559 | 27 | 0.0461 | -1.5559 | 0.1482 | `hold_no_edge` |
| `score_band` | `score_lt60` | 845 | 24 | -0.0132 | -0.5933 | 0.3333 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 146, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1278 | 799 | -0.3306 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1125 | 799 | -0.3306 | `keep_collecting` |
| `latency_state` | `simulated` | 1125 | 799 | -0.3306 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1269 | 799 | -0.3306 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1120 | 795 | -0.321 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1033 | 739 | -0.3359 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 976 | 685 | -0.3122 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 933 | 656 | -0.3317 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 817 | 583 | -0.2269 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 739 | 531 | -0.2117 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 682 | 479 | -0.3322 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 594 | 468 | -0.2776 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 623 | 409 | -0.1283 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 623 | 409 | -0.1283 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 560 | 390 | -0.5428 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 502 | 390 | -0.5428 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 502 | 390 | -0.5428 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 529 | 347 | -0.0895 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 360 | 225 | -0.4399 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 289 | 205 | -0.6547 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 258 | 191 | -0.6959 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 191 | 165 | -0.5202 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 192 | 139 | -0.271 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 176 | 125 | 0.0233 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 263 | 114 | -0.4414 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 282 | 60 | -0.2655 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 92 | 60 | -0.2655 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 216 | 60 | -0.2655 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 92 | 60 | -0.2655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 44 | 35 | 0.2829 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 35 | -0.2227 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 38 | 33 | -0.4227 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1125 | 799 | -0.8119 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1125 | 799 | -0.8119 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 628 | 594 | -1.3331 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 756 | 534 | -0.7874 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 402 | 402 | -1.3102 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 325 | 228 | -0.8452 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 161 | 161 | -1.3857 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 61 | 57 | 0.2973 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 57 | 54 | 0.823 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 39 | 39 | 0.3045 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 44 | 37 | -0.9595 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 38 | 36 | 2.3724 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 34 | 34 | 0.8742 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 58 | 31 | 0.1845 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 31 | 31 | -1.356 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 54 | 27 | -0.347 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 25 | 25 | 2.7714 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 19 | 19 | -0.3847 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.7379 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | 0.242 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 15 | 15 | 0.1772 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 15 | 15 | 0.166 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.3395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.2575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 97 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 15 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 82 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 326 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 97 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 222 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 97 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 25 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1051 | 1051 | -1.2504 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 677 | 677 | -0.91 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 669 | 669 | -0.8972 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 669 | 669 | -0.8972 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 669 | 669 | -0.8972 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 478 | 478 | -1.1549 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 322 | 322 | -1.1473 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 250 | 250 | -1.3874 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 219 | 219 | -0.4188 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 208 | 208 | -0.8535 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 207 | 207 | -1.7458 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 194 | 194 | -0.5001 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 167 | 167 | -0.5389 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 144 | 144 | -1.069 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 137 | 137 | 0.8506 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 1367 | 97 | -0.0667 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 97 | 97 | -0.0667 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 97 | 97 | -0.0667 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 91 | 91 | -1.5651 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 90 | 90 | -2.5049 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 87 | 87 | -0.8398 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 85 | 85 | -1.0571 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 62 | 62 | 0.3968 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 59 | 59 | 0.8983 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 39 | 39 | 2.6356 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 38 | 38 | 0.2111 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 34 | 34 | -0.821 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 32 | 32 | -1.4403 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 28 | 28 | 0.4117 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 27 | 27 | 0.1925 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 27 | 27 | -0.2603 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 24 | 24 | -0.0791 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 17 | 17 | 1.3267 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 15 | 15 | 0.8021 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 14 | 14 | 0.4451 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 13 | 13 | 2.8862 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 12 | 12 | 0.7229 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 8 | 8 | 1.0012 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 7 | 7 | 0.3629 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 447, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 77509 | 77509 | None | -0.5101 | 0.1753 | `hold_sample` |
| `arm` | `AVG_DOWN` | 63856 | 63552 | None | -0.7601 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 51432 | 51432 | None | -0.5078 | 0.1762 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 43789 | 43485 | None | -0.9139 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 20067 | 20067 | None | -0.4267 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 14800 | 13979 | None | 0.629 | 0.9734 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 14800 | 13979 | None | 0.629 | 0.9734 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 12812 | 12812 | None | -0.5203 | 0.1655 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 11059 | 11059 | None | 0.4798 | 0.9802 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 10662 | 10662 | None | -0.3448 | 0.1329 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 6127 | 6127 | None | -0.5143 | 0.1748 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3776 | 3776 | None | -0.4877 | 0.1835 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3362 | 3362 | None | -0.5229 | 0.1918 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1594 | 1594 | None | -0.4725 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 776 | 776 | None | -0.753 | 0.0876 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 764 | 764 | None | 3.1594 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 570 | 570 | None | -0.2906 | 0.1386 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 544 | 544 | None | -0.92 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 529 | 529 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 519 | 519 | None | -1.09 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 194 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 97 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 194 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 97 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 194 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 97 | 97 | -0.0667 | -0.089 | 0.3299 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 190 | 95 | -0.0645 | -0.086 | 0.3368 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 164 | 82 | 0.006 | 0.0079 | 0.3781 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 130 | 65 | -0.5401 | -0.7202 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 34 | 34 | -0.821 | -1.0947 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 68 | 34 | -0.821 | -1.0947 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 27 | 27 | 0.1925 | 0.2567 | 0.8519 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 27 | 27 | -0.2603 | -0.347 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 54 | 27 | 0.1925 | 0.2567 | 0.8519 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 54 | 27 | -0.2603 | -0.347 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 46 | 23 | 0.2332 | 0.3109 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 30 | 15 | -0.464 | -0.6187 | 0.0667 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |

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
