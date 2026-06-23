# Lifecycle Decision Matrix - 2026-06-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-23_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `225666`
- source_rows_total: `333342`
- retained_rows: `225666`
- dropped_rows_by_source: `{}`
- joined_rows: `202920`
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
- lifecycle_flow_bucket_count: `931`
- lifecycle_flow_complete_count: `1169`
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
| `entry` | 12639 | 1724 | 0.6969 | 0.9532 | `pass` | `NO_CHANGE` | False |
| `submit` | 4493 | 2967 | -0.507 | 0.9981 | `pass` | `NO_CHANGE` | False |
| `holding` | 4244 | 2967 | -0.9371 | 0.9978 | `pass` | `EXIT` | False |
| `scale_in` | 192130 | 189919 | -0.4333 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 12160 | 5343 | -0.9415 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 931, 'complete_flow_count': 1169, 'incomplete_flow_count': 203980, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 148747 | 148066 | -0.7288 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 41081 | 39551 | 0.6935 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1892 | 1892 | -1.0498 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 394 | 394 | 1.5747 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 301 | 301 | 1.5812 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 207 | 207 | 1.5983 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 171 | 171 | -0.1947 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 64 | 64 | -0.9353 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 38 | 38 | -0.8637 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 25 | 25 | -1.2548 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 22 | 22 | -2.0079 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 15 | 15 | -0.5468 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 15 | 15 | -0.9207 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 14 | 14 | -0.7651 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 13 | 13 | -1.3301 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 13 | 13 | -1.0217 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 13 | 13 | -0.2821 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 532, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 8565 | 1715 | 0.6973 | 0.7393 | 0.4606 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 8267 | 1292 | 0.5796 | 0.2209 | 0.4388 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 909 | 909 | 1.5781 | 2.5181 | 0.6546 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 11824 | 909 | 1.5781 | 2.5181 | 0.6546 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 9001 | 742 | -0.274 | -1.2867 | 0.2385 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2704 | 662 | 1.2778 | 2.0666 | 0.6314 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 662 | 662 | 1.2778 | 2.0666 | 0.6314 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 5479 | 644 | -0.2832 | -1.3233 | 0.2298 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 5973 | 637 | 0.0052 | -0.7603 | 0.292 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1317 | 610 | 1.0945 | 1.661 | 0.5853 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5448 | 590 | -0.2806 | -1.2487 | 0.239 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2888 | 501 | 0.6624 | 0.7148 | 0.487 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1171 | 423 | 0.9862 | 1.5676 | 0.5745 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 388 | 388 | -0.2083 | -1.9838 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 5547 | 385 | -0.2915 | -1.4137 | 0.2104 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2239 | 358 | 0.5257 | 0.3665 | 0.4218 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 476 | 245 | 1.1298 | 1.6386 | 0.5877 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1175 | 214 | 0.9496 | 1.4098 | 0.5047 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 206 | 206 | -0.249 | -2.9951 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 889 | 204 | 0.7381 | 1.0059 | 0.4951 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 193 | 193 | -0.5501 | 1.9981 | 1.0 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 1608 | 186 | -0.0545 | -0.3715 | 0.328 | `candidate_recovery_or_relax` |
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
| `actual_order_submitted` | `false` | 4357 | 2967 | -0.507 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3978 | 2967 | -0.507 | `keep_collecting` |
| `latency_state` | `simulated` | 3978 | 2967 | -0.507 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4340 | 2967 | -0.507 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3932 | 2933 | -0.4936 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3692 | 2770 | -0.5248 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3358 | 2502 | -0.5118 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3226 | 2392 | -0.5492 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2394 | 1791 | -0.5337 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2226 | 1697 | -0.6541 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2080 | 1697 | -0.6541 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2080 | 1697 | -0.6541 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2005 | 1524 | -0.6665 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2001 | 1467 | -0.3907 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1755 | 1357 | -0.6138 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1863 | 1267 | -0.3103 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1863 | 1267 | -0.3103 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1666 | 1234 | -0.3523 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1555 | 1053 | -0.2845 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1192 | 893 | -0.5433 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1000 | 725 | -0.337 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 731 | 541 | -0.2478 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 760 | 465 | -0.4812 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 322 | 262 | -0.5968 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 758 | 200 | -0.258 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 286 | 197 | -0.2568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 286 | 197 | -0.2568 | `keep_collecting` |
| `would_limit_fill` | `false` | 800 | 196 | -0.2584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 315 | 193 | -0.0383 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 49, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 3977 | 2967 | -0.9371 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3977 | 2967 | -0.9371 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2311 | 2213 | -1.4414 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2070 | 1547 | -1.0251 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1704 | 1253 | -0.8081 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1159 | 1159 | -1.5031 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 911 | 911 | -1.3641 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 252 | 231 | 0.2285 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 206 | 194 | 0.6251 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 203 | 167 | -1.0899 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 211 | 151 | 0.0645 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 143 | 143 | -1.4332 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 125 | 118 | 2.1008 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 105 | 105 | 0.3527 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 90 | 90 | 0.7393 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 129 | 60 | -0.3717 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 58 | 58 | 2.3274 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 54 | 54 | 0.1035 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 53 | 53 | 1.9487 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 35 | 35 | -0.3997 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 267 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 72 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 194 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1010 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 267 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 36 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 451 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 523 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 70 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 17 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 75, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3964 | 3964 | -1.335 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2806 | 2806 | -1.0026 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2270 | 2270 | -0.9645 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2270 | 2270 | -0.9645 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2270 | 2270 | -0.9645 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1685 | 1685 | -1.2027 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1243 | 1243 | -1.2805 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1080 | 1080 | -1.4941 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1000 | 1000 | -0.5213 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 855 | 855 | -1.7967 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 726 | 726 | -0.9341 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 613 | 613 | 0.5748 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 575 | 575 | -0.5008 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 502 | 502 | -0.5307 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 445 | 445 | -1.7116 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 421 | 421 | -1.1799 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 377 | 377 | -0.8841 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 375 | 375 | -1.2586 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 340 | 340 | -2.4384 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 7084 | 267 | -0.1033 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 267 | 267 | -0.1033 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 267 | 267 | -0.1033 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 246 | 246 | 0.2634 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 219 | 219 | 0.0879 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 208 | 208 | 0.7267 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 140 | 140 | -1.6796 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 131 | 131 | 2.4006 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 98 | 98 | -0.9684 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 91 | 91 | -0.3501 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 86 | 86 | 0.0939 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 74 | 74 | 1.1533 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 68 | 68 | -0.2912 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 60 | 60 | 0.3145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 57 | 57 | 0.7889 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 54 | 54 | 2.4854 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 47 | 47 | 0.9848 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 46 | 46 | 0.2628 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 879, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 189878 | 189878 | None | -0.5011 | 0.2046 | `hold_sample` |
| `arm` | `AVG_DOWN` | 150849 | 150168 | None | -0.801 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 107861 | 107861 | None | -0.5043 | 0.2022 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 105372 | 104691 | None | -0.9652 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 45477 | 45477 | None | -0.4229 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 41281 | 39751 | None | 0.6328 | 0.9783 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 41281 | 39751 | None | 0.6328 | 0.9783 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 35110 | 35110 | None | -0.4671 | 0.2157 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 33466 | 33466 | None | 0.5169 | 0.9819 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 24841 | 24841 | None | -0.5124 | 0.2087 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 18737 | 18737 | None | -0.3273 | 0.1613 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 12250 | 12250 | None | -0.5033 | 0.194 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 9816 | 9816 | None | -0.5568 | 0.1946 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4208 | 4208 | None | -0.459 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2651 | 2651 | None | -0.8361 | 0.0917 | `hold_sample` |
| `blocker_reason` | `ok` | 1710 | 1710 | None | -2.3962 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1487 | 1487 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1481 | 1481 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1402 | 1402 | None | 3.2431 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1315 | 1315 | None | -1.1 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 534 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 267 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 534 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 267 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 534 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 267 | 267 | -0.1033 | -0.1377 | 0.3446 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 526 | 263 | -0.1022 | -0.1363 | 0.3498 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 388 | 194 | -0.0394 | -0.0525 | 0.3711 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 350 | 175 | -0.6579 | -0.8773 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 98 | 98 | -0.9684 | -1.2912 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 196 | 98 | -0.9684 | -1.2912 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 144 | 72 | -0.2744 | -0.3658 | 0.2778 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 69 | 69 | -0.2881 | -0.3841 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 138 | 69 | -0.2881 | -0.3841 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 60 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 120 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 104 | 52 | 0.274 | 0.3654 | 1.0 | `hold_sample` |
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
