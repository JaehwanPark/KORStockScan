# Lifecycle Decision Matrix - 2026-06-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-18_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `169055`
- source_rows_total: `241955`
- retained_rows: `169055`
- dropped_rows_by_source: `{}`
- joined_rows: `153509`
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
- lifecycle_flow_bucket_count: `716`
- lifecycle_flow_complete_count: `852`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0055`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 9196 | 1236 | 0.7246 | 0.9735 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3308 | 2086 | -0.5614 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 3100 | 2086 | -0.9164 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 146603 | 144640 | -0.4398 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6848 | 3461 | -0.934 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 716, 'complete_flow_count': 852, 'incomplete_flow_count': 153274, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 114572 | 113967 | -0.7216 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 30520 | 29162 | 0.6799 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1265 | 1265 | -1.0294 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 257 | 257 | 1.8208 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 227 | 227 | 1.8703 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 138 | 138 | 1.5833 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 94 | 94 | -0.1796 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 42 | 42 | -0.8821 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 36 | 36 | -0.8186 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 22 | 22 | -0.9627 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 19 | 19 | -2.058 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 13 | 13 | -0.4741 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 12 | 12 | -0.919 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 12 | 12 | -1.2452 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 11 | 11 | -1.1447 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 10 | 10 | -0.8689 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 10 | 10 | -0.315 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 9 | 9 | -1.0011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 409, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6437 | 1231 | 0.7197 | 0.8521 | 0.4655 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 6352 | 952 | 0.6206 | 0.4227 | 0.4517 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 627 | 627 | 1.7874 | 2.8416 | 0.673 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 8587 | 627 | 1.7874 | 2.8416 | 0.673 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 6794 | 555 | -0.3531 | -1.24 | 0.2414 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 4396 | 438 | -0.3984 | -1.2697 | 0.2351 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3885 | 438 | -0.3984 | -1.2697 | 0.2351 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 4180 | 423 | -0.1895 | -0.9176 | 0.2742 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1555 | 380 | 1.4003 | 2.2652 | 0.6447 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 380 | 380 | 1.4003 | 2.2652 | 0.6447 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 812 | 361 | 1.2183 | 1.8914 | 0.6011 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1793 | 327 | 0.622 | 0.7194 | 0.4679 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 285 | 285 | -0.2558 | -1.9792 | 0.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 3683 | 262 | -0.423 | -1.4002 | 0.2061 | `hold_no_edge` |
| `score_band` | `score_70p` | 723 | 251 | 1.0907 | 1.7948 | 0.6175 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 976 | 169 | 0.5039 | 0.3005 | 0.426 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 341 | 166 | 1.3603 | 2.0114 | 0.6024 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 149 | 149 | -0.6922 | 1.9692 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 148 | 148 | -0.3728 | -2.9237 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 691 | 135 | 1.3103 | 1.7015 | 0.5111 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 135 | 135 | 1.6474 | 2.5253 | 0.7407 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 128 | 128 | 1.4235 | 2.0097 | 0.6719 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 528 | 126 | 0.6752 | 2.6973 | 0.5079 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 595 | 124 | 0.3126 | 0.4521 | 0.4194 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 1106 | 108 | -0.723 | -1.2195 | 0.2408 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 1097 | 101 | -0.1486 | -1.1691 | 0.2376 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 383 | 99 | 0.3533 | -1.1517 | 0.2424 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 87 | 87 | 1.2385 | 1.7997 | 0.6092 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 1364 | 72 | -0.2134 | -1.0042 | 0.3056 | `hold_no_edge` |
| `chosen_action` | `BUY_NOW` | 101 | 54 | -0.5389 | -0.5267 | 0.3519 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 49 | 49 | 1.01 | 1.3741 | 0.6531 | `candidate_recovery_or_relax` |
| `strength_bucket` | `neutral_strength_momentum` | 387 | 34 | -0.0599 | 0.2937 | 0.4412 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 115 | 28 | -0.1124 | -0.925 | 0.3572 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 161, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3205 | 2086 | -0.5614 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2924 | 2086 | -0.5614 | `keep_collecting` |
| `latency_state` | `simulated` | 2924 | 2086 | -0.5614 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3197 | 2086 | -0.5614 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2888 | 2061 | -0.5476 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2671 | 1922 | -0.586 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2418 | 1737 | -0.5961 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2355 | 1681 | -0.6161 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1769 | 1293 | -0.6017 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1583 | 1148 | -0.7138 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1468 | 1148 | -0.7138 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1468 | 1148 | -0.7138 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1587 | 1128 | -0.7417 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1403 | 1020 | -0.6822 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1331 | 952 | -0.4052 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1424 | 938 | -0.3749 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1424 | 938 | -0.3749 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1067 | 785 | -0.3593 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1153 | 760 | -0.358 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 902 | 620 | -0.5632 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 748 | 578 | -0.8411 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 668 | 442 | -0.3646 | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 551 | 380 | -0.2448 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 599 | 349 | -0.3887 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 280 | 169 | -0.5104 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 253 | 164 | -0.2741 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 607 | 164 | -0.2741 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 253 | 164 | -0.2741 | `keep_collecting` |
| `would_limit_fill` | `false` | 636 | 163 | -0.2761 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 208 | 160 | -0.7148 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 163 | 140 | -0.5989 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 150 | 123 | -0.3252 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 192 | 122 | -0.1051 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 187 | 112 | -0.7988 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2924 | 2086 | -0.9164 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2924 | 2086 | -0.9164 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1605 | 1540 | -1.4133 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1671 | 1171 | -1.0221 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 873 | 873 | -1.4745 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1111 | 808 | -0.7235 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 575 | 575 | -1.2994 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 189 | 173 | 0.22 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 145 | 139 | 0.5717 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 142 | 107 | -1.2147 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 155 | 107 | -0.0095 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 95 | 95 | 0.146 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 92 | 92 | -1.5441 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 86 | 85 | 1.9276 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 75 | 75 | 0.3096 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 73 | 73 | -0.0882 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 71 | 71 | 0.4514 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 62 | 62 | 0.7265 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 44 | 44 | 2.2459 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 82 | 42 | -0.3669 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 37 | 37 | 1.5712 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 32 | 32 | 0.1121 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 22 | 22 | -0.3287 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 20 | 20 | -0.4089 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.3963 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.7229 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.3238 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 176 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 49 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 127 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 838 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 176 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 35 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 303 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 500 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 19 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 46 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 36 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2563 | 2563 | -1.3119 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1787 | 1787 | -0.9802 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1498 | 1498 | -0.9662 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1498 | 1498 | -0.9662 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1498 | 1498 | -0.9662 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1115 | 1115 | -1.187 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 810 | 810 | -1.3017 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 681 | 681 | -1.4197 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 610 | 610 | -0.5354 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 496 | 496 | -0.9237 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 494 | 494 | -1.782 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 393 | 393 | 0.5555 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 387 | 387 | -0.5097 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 342 | 342 | -0.5377 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 297 | 297 | -1.2025 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 282 | 282 | -1.7004 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 231 | 231 | -0.9424 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 212 | 212 | -1.2861 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 205 | 205 | -2.3371 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3563 | 176 | -0.191 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.191 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.191 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 158 | 158 | 0.2574 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 135 | 135 | 0.6902 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 133 | 133 | 0.0405 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 85 | 85 | 2.2115 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 84 | 84 | -0.4953 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 77 | 77 | -1.6695 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 65 | 65 | -0.9924 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 61 | 61 | 0.217 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 51 | 51 | -0.3271 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 48 | 48 | 0.2369 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 46 | 46 | 1.0602 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 41 | 41 | 0.2288 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 40 | 40 | -0.2903 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 40 | 40 | 0.6673 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -0.4419 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 36 | 36 | 2.2715 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 31 | 31 | 0.9887 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 26 | 26 | -0.5387 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 519, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 144607 | 144607 | None | -0.503 | 0.1971 | `hold_sample` |
| `arm` | `AVG_DOWN` | 115978 | 115373 | None | -0.7895 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 85308 | 85308 | None | -0.5014 | 0.1987 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 80659 | 80054 | None | -0.9511 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 35319 | 35319 | None | -0.4231 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 30625 | 29267 | None | 0.6279 | 0.9749 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 30625 | 29267 | None | 0.6279 | 0.9749 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 24277 | 24277 | None | -0.4773 | 0.1987 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 24116 | 24116 | None | 0.498 | 0.9792 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 18271 | 18271 | None | -0.5174 | 0.1856 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 15354 | 15354 | None | -0.3265 | 0.1618 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 8751 | 8751 | None | -0.5175 | 0.1968 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 8000 | 8000 | None | -0.5497 | 0.2027 | `hold_sample` |
| `blocker_reason` | `low_broken` | 3339 | 3339 | None | -0.4665 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1674 | 1674 | None | -0.7999 | 0.0735 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1240 | 1240 | None | 3.2454 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1148 | 1148 | None | -2.322 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 940 | 940 | None | -0.94 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 916 | 916 | None | -0.2596 | 0.2096 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 914 | 914 | None | -0.91 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 352 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 176 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 352 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 176 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 352 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 352 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.191 | -0.2547 | 0.3636 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 254 | 127 | -0.1743 | -0.2324 | 0.3937 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 224 | 112 | -0.6824 | -0.9098 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 65 | 65 | -0.9924 | -1.3232 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 130 | 65 | -0.9924 | -1.3232 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 98 | 49 | -0.2343 | -0.3125 | 0.2857 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 48 | 48 | 0.2369 | 0.3158 | 0.8542 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 96 | 48 | 0.2369 | 0.3158 | 0.8542 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 82 | 41 | 0.2848 | 0.3798 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 40 | 40 | -0.2903 | -0.387 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 80 | 40 | -0.2903 | -0.387 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 16 | 16 | 0.8606 | 1.1475 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 32 | 16 | 0.8606 | 1.1475 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 32 | 16 | 0.8606 | 1.1475 | 1.0 | `hold_sample` |

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
