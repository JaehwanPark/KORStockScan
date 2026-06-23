# Lifecycle Decision Matrix - 2026-06-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-23_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `15855`
- source_rows_total: `19569`
- retained_rows: `15855`
- dropped_rows_by_source: `{}`
- joined_rows: `10372`
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
- lifecycle_flow_bucket_count: `254`
- lifecycle_flow_complete_count: `178`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0138`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2142 | 227 | 0.6588 | 0.8064 | `pass` | `NO_CHANGE` | False |
| `submit` | 563 | 343 | -0.2588 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 564 | 343 | -1.0189 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 9040 | 8794 | -0.4602 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3546 | 665 | -0.8896 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 254, 'complete_flow_count': 178, 'incomplete_flow_count': 12758, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6509 | 6435 | -0.8784 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2219 | 2047 | 0.8851 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 229 | 229 | -1.0142 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 81 | 81 | 1.6659 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 37 | 37 | 0.1543 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 25 | 25 | -0.1561 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 9 | 9 | -1.1156 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -1.3662 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 7 | 7 | 4.5946 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.6133 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2b39f2b635` | 4 | 4 | -1.3141 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 4 | 4 | -1.4109 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 4 | 4 | -1.8443 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 4 | 4 | 2.8836 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:23495871ee` | 3 | 3 | -1.9545 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:63d49cf2a2` | 3 | 3 | -1.03 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 3 | 3 | -1.6903 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -0.3195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 3 | 3 | 0.584 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 281, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1572 | 225 | 0.6756 | 0.2286 | 0.3645 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1449 | 183 | 0.565 | -0.4089 | 0.3278 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 906 | 136 | 0.6618 | 0.3894 | 0.4044 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 321 | 120 | 0.9854 | 1.1808 | 0.475 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 115 | 115 | 1.3977 | 2.1485 | 0.5565 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2030 | 115 | 1.3977 | 2.1485 | 0.5565 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 476 | 115 | 1.3977 | 2.1485 | 0.5565 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 115 | 115 | 1.3977 | 2.1485 | 0.5565 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1198 | 112 | -0.1 | -1.7801 | 0.1697 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 318 | 112 | 1.108 | 1.4318 | 0.4732 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1310 | 95 | 0.4144 | -0.7562 | 0.2421 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1597 | 94 | -0.0918 | -1.8291 | 0.1808 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 696 | 73 | 0.881 | 0.6552 | 0.3699 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1242 | 62 | -0.0276 | -2.041 | 0.1451 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 556 | 59 | 0.089 | -1.4044 | 0.2203 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 947 | 53 | -0.3104 | -2.1983 | 0.1132 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 51 | 51 | -0.1104 | -2.0616 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 42 | 42 | 0.119 | -3.3281 | 0.0 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 281 | 36 | -0.1313 | 0.7154 | 0.4722 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 36 | 36 | 0.8668 | 0.9375 | 0.5833 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 29 | 29 | 1.2184 | 1.7027 | 0.5172 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 67 | 29 | -0.1749 | -0.524 | 0.3448 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 138 | 20 | 0.321 | -1.7605 | 0.2 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 110, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 560 | 343 | -0.2588 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 516 | 343 | -0.2588 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 516 | 343 | -0.2588 | `keep_collecting` |
| `latency_state` | `simulated` | 516 | 343 | -0.2588 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 557 | 343 | -0.2588 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 516 | 343 | -0.2588 | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 513 | 341 | -0.2595 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 513 | 338 | -0.2492 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 455 | 300 | -0.2802 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 434 | 284 | -0.2545 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 436 | 283 | -0.2914 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 384 | 257 | -0.2974 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 272 | 198 | -0.3563 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 261 | 198 | -0.3563 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 261 | 198 | -0.3563 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 252 | 142 | -0.1212 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 252 | 142 | -0.1212 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 250 | 141 | -0.1231 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 159 | 122 | -0.5943 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 182 | 98 | 0.0099 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 113 | 71 | -0.1756 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 80 | 58 | -0.2933 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 77 | 58 | -0.1038 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 37 | -0.1816 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 50 | 35 | -0.1359 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 21 | 0.0815 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 33 | 17 | -0.3767 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 14 | -0.4514 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 29 | 12 | 0.0953 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 21 | 11 | 0.3792 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 11 | 8 | 0.0079 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 6 | -0.5865 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 6 | -0.3481 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 50 | 5 | -0.9102 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_not_available` | 39 | 3 | -0.334 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 515 | 343 | -1.0189 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 515 | 343 | -1.0189 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 422 | 274 | -0.98 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 284 | 270 | -1.5216 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 210 | 210 | -1.5287 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 79 | 56 | -1.0881 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 47 | 47 | -1.4849 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 28 | 22 | 0.9613 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 20 | 20 | 0.8832 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 19 | 15 | 0.3526 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 15 | 15 | 0.3526 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 17 | 14 | 2.7705 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 14 | 13 | -1.5388 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 13 | 13 | -1.5388 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 26 | 12 | -0.3942 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 10 | 0.0864 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.388 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 10 | 10 | 3.3099 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | 0.0372 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.4219 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 49 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 41 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 172 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 49 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 148 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 485 | 485 | -1.3764 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 311 | 311 | -1.1743 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 305 | 305 | -0.7951 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 305 | 305 | -0.7951 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 305 | 305 | -0.7951 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 204 | 204 | -1.2137 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 141 | 141 | -1.8034 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 129 | 129 | -1.6071 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 126 | 126 | -1.2044 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 110 | 110 | -0.594 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 80 | 80 | -0.4439 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 72 | 72 | -1.2853 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 67 | 67 | -0.4745 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 61 | 61 | -1.333 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 58 | 58 | -1.6501 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2930 | 49 | 0.3298 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.3298 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.3298 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 46 | 46 | -2.5154 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 43 | 43 | 0.9413 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 35 | 35 | -1.0543 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 34 | 34 | -1.6841 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 33 | 33 | -0.5801 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 30 | 30 | 0.169 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 27 | 27 | 1.0262 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 22 | 22 | 0.5308 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 21 | 21 | 3.1936 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 20 | 20 | 0.2335 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 14 | 14 | -0.9964 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 13 | 13 | -0.2862 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 9 | 9 | 0.155 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 9 | 9 | -0.0284 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 7 | 7 | 1.06 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.2514 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 0.9643 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 7 | 7 | 1.7128 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 7 | 7 | 2.9523 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 6 | 6 | 1.5112 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 4 | 4 | 4.8424 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 384, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 8786 | 8786 | None | -0.515 | 0.2362 | `hold_sample` |
| `arm` | `AVG_DOWN` | 6768 | 6694 | None | -0.9431 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4847 | 4773 | None | -1.1646 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 4731 | 4731 | None | -0.5442 | 0.2526 | `hold_sample` |
| `arm` | `PYRAMID` | 2272 | 2100 | None | 0.8488 | 0.99 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2272 | 2100 | None | 0.8488 | 0.99 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 1921 | 1921 | None | -0.3926 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1681 | 1681 | None | 0.5582 | 0.9917 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 1595 | 1595 | None | -0.5128 | 0.2188 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1257 | 1257 | None | -0.4645 | 0.2442 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 645 | 645 | None | -0.3867 | 0.1969 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 558 | 558 | None | -0.5364 | 0.1738 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 420 | 420 | None | -0.8489 | 0.1643 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 257 | 257 | None | -0.4075 | 0.1323 | `hold_sample` |
| `blocker_reason` | `ok` | 237 | 237 | None | -2.7045 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 178 | 178 | None | -0.4053 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 162 | 162 | None | 3.2259 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 134 | 134 | None | -0.27 | 0.3582 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 117 | 117 | None | -0.5143 | 0.188 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.41)` | 95 | 95 | None | -1.41 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 98 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 49 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 98 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 49 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 98 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 49 | 49 | 0.3298 | 0.4398 | 0.4082 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 90 | 45 | 0.3745 | 0.4993 | 0.4444 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 82 | 41 | 0.4215 | 0.562 | 0.4146 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 58 | 29 | -0.6137 | -0.8183 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 14 | 14 | -0.9964 | -1.3286 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 14 | 14 | -0.2711 | -0.3614 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 28 | 14 | -0.9964 | -1.3286 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 28 | 14 | -0.2711 | -0.3614 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 8 | 8 | 0.1837 | 0.245 | 0.875 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 16 | 8 | 0.1837 | 0.245 | 0.875 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.135 | -0.18 | 0.4286 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 14 | 7 | 0.2175 | 0.29 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 6 | 6 | 1.5112 | 2.015 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300` | 12 | 6 | 1.5112 | 2.015 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 12 | 6 | 1.5112 | 2.015 | 1.0 | `hold_sample` |

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
