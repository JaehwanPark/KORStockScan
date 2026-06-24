# Lifecycle Decision Matrix - 2026-06-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-24_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `18932`
- source_rows_total: `23561`
- retained_rows: `18932`
- dropped_rows_by_source: `{}`
- joined_rows: `12179`
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
- lifecycle_flow_bucket_count: `225`
- lifecycle_flow_complete_count: `153`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0095`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2050 | 252 | 0.7129 | 0.8642 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 568 | 326 | -0.4842 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 562 | 326 | -1.1317 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 10901 | 10590 | -0.4633 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4851 | 685 | -0.9315 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 225, 'complete_flow_count': 153, 'incomplete_flow_count': 15901, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8124 | 8038 | -0.8213 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2436 | 2211 | 0.8836 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 273 | 273 | -0.9741 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 75 | 75 | 1.2116 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 50 | 50 | 1.564 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 34 | 34 | 0.1541 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 15 | 15 | 3.1107 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.8041 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.6133 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 4 | 4 | -1.4109 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 4 | 4 | -1.8443 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 4 | 4 | -0.8548 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 3 | 3 | -1.8864 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 3 | 3 | 2.7581 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ee117bc3cd` | 3 | 3 | -2.2338 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -1.5033 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:b24470d667` | 2 | 2 | -1.415 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:4fa8c887a4` | 2 | 2 | -0.4466 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 304, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1458 | 250 | 0.7284 | 0.6999 | 0.412 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1310 | 192 | 0.6425 | 0.2097 | 0.3802 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 142 | 142 | 1.5019 | 2.3598 | 0.5774 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1940 | 142 | 1.5019 | 2.3598 | 0.5774 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 142 | 142 | 1.5019 | 2.3598 | 0.5774 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1128 | 110 | -0.3057 | -1.4895 | 0.2 | `hold_no_edge` |
| `score_band` | `score_70p` | 293 | 102 | 0.8054 | 1.04 | 0.4902 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1461 | 94 | -0.3279 | -1.5031 | 0.2128 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 598 | 84 | 0.2886 | 0.0157 | 0.4048 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 202 | 74 | 0.8552 | 1.0394 | 0.5135 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 350 | 65 | 1.3195 | 1.9997 | 0.5846 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 799 | 62 | 0.0954 | -0.9838 | 0.2097 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1125 | 59 | -0.3899 | -1.9141 | 0.1356 | `hold_no_edge` |
| `score_band` | `score_66_69` | 108 | 53 | 1.4538 | 2.3372 | 0.5283 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 52 | 52 | -0.2175 | -2.0206 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 314 | 50 | 0.3562 | 1.2754 | 0.52 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 465 | 49 | 0.9596 | 0.7141 | 0.3878 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 548 | 41 | -0.4616 | -2.2578 | 0.1219 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 361 | 39 | -0.1125 | -1.0843 | 0.2564 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 35 | 35 | -0.3287 | -3.3271 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 25 | 25 | 1.0659 | 1.2688 | 0.64 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 24 | 24 | 1.4903 | 2.1754 | 0.625 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 12 | 12 | 2.0293 | 3.4187 | 0.75 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 112, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 557 | 326 | -0.4842 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 530 | 326 | -0.4842 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 530 | 326 | -0.4842 | `keep_collecting` |
| `latency_state` | `simulated` | 530 | 326 | -0.4842 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 557 | 326 | -0.4842 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 530 | 326 | -0.4842 | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 525 | 324 | -0.4863 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 526 | 320 | -0.4851 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 470 | 284 | -0.5409 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 447 | 268 | -0.5292 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 441 | 257 | -0.5603 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 404 | 254 | -0.5039 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 277 | 187 | -0.6165 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 264 | 187 | -0.6165 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 264 | 187 | -0.6165 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 263 | 136 | -0.3055 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 263 | 136 | -0.3055 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 260 | 135 | -0.3088 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 170 | 120 | -0.845 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 186 | 93 | -0.1559 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 87 | 67 | -0.2024 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 81 | 57 | -0.2906 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 93 | 47 | -0.6501 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 52 | 36 | -0.0921 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 26 | 23 | -0.187 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 47 | 21 | -0.0117 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 30 | 20 | -1.1682 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 16 | -0.4684 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 12 | 0.4284 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 10 | -0.5136 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 27 | 8 | -1.0075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 7 | -0.6102 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 8 | 6 | -0.1551 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 42 | 6 | -0.4354 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 6 | 1.411 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 529 | 326 | -1.1317 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 529 | 326 | -1.1317 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 440 | 264 | -1.1154 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 268 | 259 | -1.5771 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 206 | 206 | -1.5784 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 80 | 55 | -1.1099 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 46 | 46 | -1.5194 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 24 | 21 | 0.7307 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.6242 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 18 | 14 | 0.3645 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 14 | 14 | 0.3645 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 14 | 13 | 2.1084 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 17 | 11 | -0.4343 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.5308 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 2.4135 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 18 | 8 | -0.4425 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 9 | 7 | -1.9177 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -1.9177 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.4483 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.4219 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 33 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 23 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 203 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 33 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 176 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 25 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 60, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 506 | 506 | -1.3736 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 340 | 340 | -0.8194 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 340 | 340 | -0.8194 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 340 | 340 | -0.8194 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 312 | 312 | -1.1581 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 236 | 236 | -1.1723 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 134 | 134 | -1.2604 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 128 | 128 | -1.7448 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 127 | 127 | -1.8914 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 118 | 118 | -0.4683 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 80 | 80 | -0.4622 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 71 | 71 | -0.481 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 66 | 66 | -1.2534 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 66 | 66 | -1.7302 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 57 | 57 | -1.3888 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 44 | 44 | 1.1106 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 40 | 40 | -2.6696 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 40 | 40 | -0.6178 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 4199 | 33 | 0.057 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 33 | 33 | 0.057 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 33 | 33 | 0.057 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 32 | 32 | -0.0082 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 30 | 30 | -1.8086 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 28 | 28 | -1.0712 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 27 | 27 | 1.0138 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 21 | 21 | 0.2347 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 20 | 20 | 0.5062 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 20 | 20 | 2.8361 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 10 | 10 | 1.9281 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 9 | 9 | -1.0317 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 9 | 9 | -0.3142 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 9 | 9 | 2.9845 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 8 | 8 | -0.3109 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 6 | 6 | 1.0083 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.3497 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 5 | 5 | -0.4554 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 0.8147 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 4 | 4 | 4.3515 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 376, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 10581 | 10581 | None | -0.5151 | 0.2032 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8424 | 8338 | None | -0.883 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5978 | 5892 | None | -1.0865 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 5361 | 5361 | None | -0.4713 | 0.2399 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2446 | 2446 | None | -0.393 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 2477 | 2252 | None | 0.8504 | 0.9569 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2477 | 2252 | None | 0.8504 | 0.9569 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2200 | 2200 | None | -0.5498 | 0.1727 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1736 | 1736 | None | 0.5038 | 0.9637 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1586 | 1586 | None | -0.5767 | 0.169 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 739 | 739 | None | -0.5156 | 0.1583 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 695 | 695 | None | -0.6025 | 0.1425 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 529 | 529 | None | -0.3796 | 0.0889 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 416 | 416 | None | -0.8633 | 0.1202 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 283 | 283 | None | -1.07 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 272 | 272 | None | -0.4266 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 223 | 223 | None | 3.1369 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 221 | 221 | None | -2.6652 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 156 | 156 | None | -0.3072 | 0.3398 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 129 | 129 | None | -0.5495 | 0.1705 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 66 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 33 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 66 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 33 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 66 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 33 | 33 | 0.057 | 0.0761 | 0.3939 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 62 | 31 | 0.0718 | 0.0958 | 0.4194 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 46 | 23 | 0.2237 | 0.2983 | 0.4348 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 40 | 20 | -0.612 | -0.816 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 10 | 10 | -0.2902 | -0.387 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 20 | 10 | -0.2902 | -0.387 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.0317 | -1.3755 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 18 | 9 | -1.0317 | -1.3755 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.12 | -0.16 | 0.6 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.2745 | 0.366 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |

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
