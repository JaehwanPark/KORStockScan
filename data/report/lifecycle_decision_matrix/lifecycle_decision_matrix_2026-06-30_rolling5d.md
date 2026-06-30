# Lifecycle Decision Matrix - 2026-06-30

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-30_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20421`
- source_rows_total: `36827`
- retained_rows: `20421`
- dropped_rows_by_source: `{}`
- joined_rows: `11391`
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
- lifecycle_flow_bucket_count: `161`
- lifecycle_flow_complete_count: `68`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0036`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1678 | 217 | 0.8865 | 0.8901 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 302 | 138 | -0.4194 | 0.9707 | `pass` | `NO_CHANGE` | False |
| `holding` | 229 | 138 | -0.799 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 10868 | 10643 | -0.5897 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7344 | 255 | -0.8667 | 0.5099 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 161, 'complete_flow_count': 68, 'incomplete_flow_count': 18636, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8268 | 8211 | -0.9983 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2464 | 2296 | 0.8799 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 106 | 106 | -1.0297 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 81 | 81 | 0.8705 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 57 | 57 | 1.5471 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 17 | 17 | 2.8244 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 15 | 15 | -0.4371 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -0.6 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 3 | 3 | -2.3956 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -0.9967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 2 | 2 | -0.9762 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f1afdbf31e` | 2 | 2 | -2.3266 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:4badedabe9` | 2 | 2 | -0.7389 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2089125172` | 2 | 2 | -1.0394 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 2 | 2 | -0.66 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 2 | 2 | -0.875 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce511c4ca6` | 1 | 1 | -1.4427 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:acadf41d1b` | 1 | 1 | -1.1508 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89550e9954` | 1 | 1 | -2.0794 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:65ec45aaab` | 1 | 1 | -1.6151 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 318, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1314 | 217 | 0.8865 | 1.2913 | 0.5069 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1069 | 162 | 1.0048 | 1.3339 | 0.5309 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 174 | 155 | 1.3336 | 2.186 | 0.5806 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1616 | 155 | 1.3336 | 2.186 | 0.5806 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 212 | 83 | 1.6624 | 2.6486 | 0.6386 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 83 | 83 | 1.6624 | 2.6486 | 0.6386 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 155 | 70 | 1.0122 | 1.7615 | 0.5857 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1284 | 58 | -0.2735 | -0.909 | 0.3275 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 434 | 48 | 0.5142 | 0.4008 | 0.3958 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 509 | 47 | -0.4 | -1.2259 | 0.2553 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 228 | 43 | 1.6738 | 2.3425 | 0.5814 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 155 | 38 | 0.581 | 0.5445 | 0.4474 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 187 | 36 | 1.0505 | 2.179 | 0.6667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 295 | 35 | 0.3856 | 0.7535 | 0.4285 | `hold_no_edge` |
| `score_band` | `score_60_62` | 431 | 34 | -0.5817 | -0.9956 | 0.2941 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 75 | 34 | 1.8804 | 3.1917 | 0.7353 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 244 | 32 | -0.1223 | -0.8604 | 0.25 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 384 | 28 | -0.4847 | -1.1672 | 0.25 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | -0.0133 | -2.36 | 0.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 24 | 24 | 0.6611 | 0.9481 | 0.4583 | `hold_sample` |
| `stale_bucket` | `fresh` | 171 | 19 | -0.275 | -1.3127 | 0.2632 | `hold_no_edge` |
| `time_bucket` | `time_1400_close` | 219 | 19 | 0.7002 | 0.5567 | 0.421 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 13 | 13 | -0.1191 | -3.69 | 0.0 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 113, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 235 | 138 | -0.4194 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 217 | 138 | -0.4194 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 217 | 138 | -0.4194 | `keep_collecting` |
| `latency_state` | `simulated` | 217 | 138 | -0.4194 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 235 | 138 | -0.4194 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 217 | 138 | -0.4194 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 204 | 131 | -0.4128 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 165 | 112 | -0.4678 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 154 | 97 | -0.2729 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 154 | 97 | -0.2729 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 128 | 94 | -0.4953 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 112 | 84 | -0.3504 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 99 | 82 | -0.3275 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 97 | 71 | -0.474 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 187 | 53 | -0.4712 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 65 | 53 | -0.2857 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 89 | 44 | -0.2573 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 92 | 44 | -0.2573 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 89 | 44 | -0.2573 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 66 | 41 | -0.7662 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 63 | 41 | -0.7662 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 63 | 41 | -0.7662 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 49 | 40 | -0.1549 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 54 | 26 | -0.2111 | `keep_collecting` |
| `would_limit_fill` | `true` | 48 | 25 | -0.066 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 26 | 22 | -0.5653 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 26 | 20 | -0.6167 | `keep_collecting` |
| `would_limit_fill` | `false` | 126 | 19 | -0.5091 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 31 | 15 | 0.2513 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 33 | 15 | -0.5004 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 29 | 12 | -1.6417 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 17 | 10 | -0.542 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 9 | -0.5582 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -0.7944 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 12 | 6 | -0.6932 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 217 | 138 | -0.799 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 217 | 138 | -0.799 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 207 | 129 | -0.8834 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 89 | 85 | -1.6806 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 80 | 80 | -1.7058 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 21 | 18 | 0.1403 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.0701 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 13 | 12 | 1.6501 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 15 | 11 | -0.2273 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 11 | 11 | 1.1381 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.2273 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 1.1381 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.227 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 5 | -0.0464 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 4 | 4 | 0.9825 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -1.2115 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.3796 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.3343 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 79 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 78 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 58, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 164 | 164 | -1.4217 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 134 | 134 | -0.9267 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 134 | 134 | -0.9267 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 134 | 134 | -0.9267 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 109 | 109 | -0.9094 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 88 | 88 | -1.2272 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 51 | 51 | -0.4605 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 48 | 48 | -1.3917 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 44 | 44 | -1.338 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 41 | 41 | -0.5268 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 34 | 34 | -0.5537 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 28 | 28 | -2.2199 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 27 | 27 | -0.5 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | 0.7802 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 19 | 19 | -1.8351 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 16 | 16 | 0.3713 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 14 | 14 | -2.765 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.0654 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 7101 | 12 | 0.1906 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 12 | 1.7909 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1906 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1906 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 11 | 11 | -0.8262 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 10 | 10 | 0.2207 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 9 | 9 | 0.8712 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.8372 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 1.0783 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.3825 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -1.035 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 4 | 4 | 0.7488 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 1.1064 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1233 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 3 | 3 | 0.82 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -1.4085 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 2 | 2 | 0.0958 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.06 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 0.965 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.8194 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 381, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 10637 | 10637 | None | -0.6598 | 0.2078 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8387 | 8330 | None | -1.0654 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 7829 | 7772 | None | -1.0764 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 6768 | 6768 | None | -0.6247 | 0.2358 | `hold_sample` |
| `arm` | `PYRAMID` | 2481 | 2313 | None | 0.804 | 0.958 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2481 | 2313 | None | 0.804 | 0.958 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2223 | 2223 | None | -0.7812 | 0.1484 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1904 | 1904 | None | 0.5736 | 0.9832 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 779 | 779 | None | -0.6365 | 0.1656 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 558 | 558 | None | -0.9124 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 520 | 520 | None | -0.6136 | 0.175 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 347 | 347 | None | -0.6876 | 0.1873 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.46)` | 206 | 206 | None | -1.46 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 204 | 204 | None | -0.97 | 0.0 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 202 | 202 | None | -1.0876 | 0.0297 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.68)` | 187 | 187 | None | -1.68 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 186 | 186 | None | -0.6856 | 0.1613 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 28, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 24 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 12 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 24 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `stage` | `exit` | 12 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 24 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | 0.1906 | 0.2542 | 0.3333 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | 0.2236 | 0.2982 | 0.3636 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 10 | 0.411 | 0.548 | 0.4 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.6272 | -0.8363 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.035 | -1.38 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.035 | -1.38 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.82 | 1.0933 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.9113 | -1.215 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 2 | 1 | 4.845 | 6.46 | 1.0 | `hold_sample` |

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
