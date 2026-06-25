# Lifecycle Decision Matrix - 2026-06-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-25_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `95646`
- source_rows_total: `123939`
- retained_rows: `95646`
- dropped_rows_by_source: `{}`
- joined_rows: `79637`
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
- lifecycle_flow_bucket_count: `558`
- lifecycle_flow_complete_count: `573`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0067`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 7453 | 911 | 1.0987 | 0.9518 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1659 | 1050 | -0.4391 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1582 | 1050 | -0.9609 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 76133 | 74704 | -0.4223 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 8819 | 1922 | -0.8994 | 0.986 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 558, 'complete_flow_count': 573, 'incomplete_flow_count': 85576, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 59319 | 58945 | -0.7085 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 15945 | 14890 | 0.7285 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 684 | 684 | -0.9815 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 247 | 247 | 1.6564 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 203 | 203 | 2.0775 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 98 | 98 | 2.5 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 74 | 74 | -0.1322 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 26 | 26 | -0.9873 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 21 | 21 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 18 | 18 | -0.9614 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 15 | 15 | -2.1039 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 12 | 12 | -0.7925 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 11 | 11 | -1.0045 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 9 | 9 | -1.4566 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 9 | 9 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 8 | 8 | -0.5944 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 8 | 8 | -1.3143 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 6 | 6 | -2.6958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 6 | 6 | -0.5667 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 465, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5531 | 904 | 1.0992 | 1.3128 | 0.4856 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 5492 | 733 | 0.7859 | 0.6077 | 0.4597 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 555 | 555 | 1.9515 | 3.0228 | 0.6595 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 7097 | 555 | 1.9515 | 3.0228 | 0.6595 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 422 | 422 | 1.8743 | 2.9325 | 0.6422 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 1050 | 345 | 1.923 | 2.9925 | 0.658 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 948 | 324 | 1.204 | 1.7634 | 0.5586 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 813 | 322 | 1.6025 | 2.3258 | 0.6025 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 5772 | 306 | -0.2236 | -1.3943 | 0.219 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3806 | 272 | -0.2438 | -1.4517 | 0.1948 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 3644 | 241 | 0.3807 | -0.3612 | 0.2946 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 176 | 176 | -0.1676 | -1.9825 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 1214 | 172 | 1.4477 | 1.9717 | 0.5581 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 2750 | 171 | -0.1385 | -1.3037 | 0.2164 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1121 | 170 | 0.5465 | 0.1446 | 0.3647 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 359 | 168 | 1.8893 | 2.9247 | 0.6131 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 3616 | 148 | -0.2214 | -1.8203 | 0.1419 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 789 | 121 | 1.573 | 2.7593 | 0.5703 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 109 | 109 | 1.5528 | 2.3776 | 0.7156 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 98 | 98 | -0.1636 | -3.155 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 92 | 92 | 1.502 | 2.0377 | 0.6413 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 554 | 86 | 1.2888 | 1.9529 | 0.5233 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 72 | 72 | -0.2875 | 2.38 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 373 | 64 | 0.4484 | -1.4509 | 0.2031 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 64 | 64 | 0.7985 | 0.8395 | 0.6406 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 54 | 54 | 1.4048 | 1.7792 | 0.6482 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 169 | 50 | -0.275 | -1.038 | 0.18 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 222 | 44 | 4.5084 | 7.9531 | 0.6364 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 572 | 41 | -0.2866 | -0.9324 | 0.2927 | `hold_no_edge` |
| `score_band` | `score_lt60` | 915 | 25 | -0.2566 | -0.8788 | 0.36 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 16 | 16 | 1.7477 | 2.88 | 0.6875 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 162, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1615 | 1050 | -0.4391 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1464 | 1050 | -0.4391 | `keep_collecting` |
| `latency_state` | `simulated` | 1464 | 1050 | -0.4391 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1606 | 1050 | -0.4391 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1453 | 1043 | -0.4288 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1396 | 1001 | -0.4398 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1341 | 944 | -0.4303 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1206 | 860 | -0.4167 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1208 | 846 | -0.4554 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1157 | 817 | -0.4159 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1080 | 761 | -0.4105 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 983 | 701 | -0.4535 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 767 | 552 | -0.5891 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 707 | 552 | -0.5891 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 707 | 552 | -0.5891 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 754 | 495 | -0.2725 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 754 | 495 | -0.2725 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 680 | 442 | -0.2357 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 377 | 300 | -0.6838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 391 | 243 | -0.1477 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 308 | 236 | -0.5373 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 266 | 205 | -0.6005 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 330 | 203 | -0.4512 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 251 | 197 | -0.3147 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 283 | 106 | -0.5173 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 155 | 93 | -0.3409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 86 | 58 | -0.009 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 169 | 52 | -0.4194 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 263 | 49 | -0.4247 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 68 | 49 | -0.4247 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 68 | 49 | -0.4247 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 60 | 47 | -0.522 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 59 | 45 | -1.0826 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 59 | 42 | -0.212 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 39 | 37 | -0.3066 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1463 | 1050 | -0.9609 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1463 | 1050 | -0.9609 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 837 | 798 | -1.4624 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1068 | 747 | -0.9688 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 569 | 569 | -1.4703 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 342 | 258 | -0.9046 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 190 | 190 | -1.4318 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 77 | 71 | 0.8275 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 73 | 65 | 0.2174 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 52 | 52 | 0.7715 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 48 | 48 | 0.1977 | `hold_no_edge` |
| `holding_action` | `BUY` | 53 | 45 | -1.1517 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 47 | 44 | 2.3075 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 39 | 39 | -1.4965 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 68 | 38 | 0.0444 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 67 | 34 | -0.5306 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 30 | 30 | 2.6806 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.6128 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 23 | 23 | -0.0789 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 18 | 18 | 0.9961 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 15 | 15 | 0.2297 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 14 | 14 | 0.2093 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 1.4204 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.3022 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 119 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 17 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 96 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 413 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 119 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 321 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 84 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 69, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1396 | 1396 | -1.3336 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 947 | 947 | -1.0383 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 856 | 856 | -0.8701 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 856 | 856 | -0.8701 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 856 | 856 | -0.8701 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 592 | 592 | -1.1807 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 433 | 433 | -1.2173 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 374 | 374 | -1.5593 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 330 | 330 | -1.8204 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 316 | 316 | -0.457 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 257 | 257 | -0.9948 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 245 | 245 | -0.5021 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 210 | 210 | -0.5119 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 170 | 170 | 0.9149 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 158 | 158 | -1.663 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 157 | 157 | -1.0964 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 137 | 137 | -1.1795 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 129 | 129 | -2.5923 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 7016 | 119 | -0.004 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 119 | 119 | -0.004 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 119 | 119 | -0.004 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 117 | 117 | -0.7883 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 81 | 81 | 0.95 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 78 | 78 | 0.3334 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 68 | 68 | 0.1154 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 64 | 64 | -1.6365 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 54 | 54 | 2.6913 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 39 | 39 | -0.8725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 33 | 33 | 0.2515 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 32 | 32 | -0.2583 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 31 | 31 | 0.187 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 29 | 29 | 0.2552 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 28 | 28 | -0.2852 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 27 | 27 | 1.6043 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 21 | 21 | 0.7696 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 18 | 18 | 3.0536 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 15 | 15 | 0.4145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 13 | 13 | 0.9954 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 13 | 13 | 0.7629 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 9 | 9 | -1.254 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 692, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 74673 | 74673 | None | -0.4779 | 0.1946 | `hold_sample` |
| `arm` | `AVG_DOWN` | 60093 | 59719 | None | -0.7676 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 49721 | 49721 | None | -0.4737 | 0.1979 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 40901 | 40527 | None | -0.9341 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 19192 | 19192 | None | -0.416 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 16040 | 14985 | None | 0.6796 | 0.9711 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 16040 | 14985 | None | 0.6796 | 0.9711 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 12842 | 12842 | None | -0.4911 | 0.1821 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 11834 | 11834 | None | 0.4773 | 0.9785 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 9436 | 9436 | None | -0.341 | 0.1335 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 6076 | 6076 | None | -0.4949 | 0.1913 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3500 | 3500 | None | -0.4803 | 0.1949 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2534 | 2534 | None | -0.4475 | 0.2012 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1579 | 1579 | None | -0.4495 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1019 | 1019 | None | -0.8131 | 0.1099 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 993 | 993 | None | 3.2625 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 654 | 654 | None | -0.3468 | 0.3486 | `hold_sample` |
| `blocker_reason` | `ok` | 648 | 648 | None | -2.4816 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 520 | 520 | None | -0.2667 | 0.1346 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 512 | 512 | None | -1.09 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 238 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 119 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 238 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `stage` | `exit` | 119 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 238 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 119 | 119 | -0.004 | -0.0053 | 0.3613 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 230 | 115 | 0.0019 | 0.0025 | 0.3739 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 192 | 96 | 0.0909 | 0.1211 | 0.4062 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 152 | 76 | -0.5601 | -0.7468 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 39 | 39 | -0.8725 | -1.1633 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 78 | 39 | -0.8725 | -1.1633 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 33 | 33 | -0.2527 | -0.337 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 66 | 33 | -0.2527 | -0.337 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 30 | 30 | 0.1957 | 0.261 | 0.8667 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 60 | 30 | 0.1957 | 0.261 | 0.8667 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_zero_pos080` | 52 | 26 | 0.2337 | 0.3115 | 1.0 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 34 | 17 | -0.3702 | -0.4935 | 0.2353 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 8 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 16 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 8 | 0.8344 | 1.1125 | 1.0 | `hold_sample` |

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
