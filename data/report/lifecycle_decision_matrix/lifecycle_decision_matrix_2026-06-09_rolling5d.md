# Lifecycle Decision Matrix - 2026-06-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-09_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `59060`
- source_rows_total: `104047`
- retained_rows: `59060`
- dropped_rows_by_source: `{}`
- joined_rows: `55947`
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
- lifecycle_flow_bucket_count: `261`
- lifecycle_flow_complete_count: `272`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.005`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2628 | 458 | 0.925 | 1.0 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 899 | 808 | -0.4583 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 848 | 808 | -0.9171 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 52387 | 52384 | -0.3634 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2298 | 1489 | -0.9739 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 261, 'complete_flow_count': 272, 'incomplete_flow_count': 54456, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 38371 | 38368 | -0.7164 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 13332 | 13332 | 0.6794 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 596 | 596 | -1.1206 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 121 | 121 | 1.516 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 79 | 79 | 1.5258 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 79 | 79 | 1.8929 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 50 | 50 | -0.4894 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 15 | 15 | -0.956 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 9 | 9 | -0.8733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 6 | 6 | -1.771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c6e869aefc` | 5 | 5 | -0.9751 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 4 | 4 | -0.9947 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 4 | 4 | -1.2533 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 4 | 4 | -0.9298 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -0.9324 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5035e8a5e2` | 4 | 4 | -1.0158 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b9576c8a52` | 4 | 4 | -0.8943 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.7375 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fddb29efa4` | 3 | 3 | -1.0195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 3 | 3 | -1.7012 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 290, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1537 | 458 | 0.925 | 1.2483 | 0.5328 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1338 | 302 | 0.6942 | 0.5348 | 0.5099 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 279 | 279 | 1.6255 | 2.6571 | 0.6846 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2449 | 279 | 1.6255 | 2.6571 | 0.6846 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 660 | 165 | 0.952 | 1.5793 | 0.6606 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 165 | 165 | 0.952 | 1.5793 | 0.6606 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1529 | 163 | -0.1272 | -1.0326 | 0.2699 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 172 | 127 | 0.8948 | 1.4888 | 0.6536 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 466 | 119 | 0.3704 | -0.2043 | 0.395 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 399 | 101 | 0.6349 | 0.7433 | 0.6336 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 357 | 92 | 0.0528 | -1.0085 | 0.2826 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 448 | 91 | 0.0578 | -1.0312 | 0.2747 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 83 | 83 | -0.1966 | -1.9795 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_ok` | 195 | 73 | 1.6534 | 3.6187 | 0.6438 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 269 | 68 | 1.0944 | 1.2719 | 0.5 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 300 | 67 | 0.8406 | 0.9577 | 0.4776 | `hold_sample` |
| `score_band` | `score_63_65` | 128 | 66 | 1.1687 | 1.647 | 0.6212 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 569 | 61 | 0.0052 | -0.8339 | 0.2951 | `hold_no_edge` |
| `score_band` | `score_70p` | 122 | 58 | 0.2964 | 0.9368 | 0.6034 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 357 | 53 | 0.2457 | 0.5184 | 0.4528 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | -0.1917 | 1.856 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 35 | 35 | 0.8978 | 1.0387 | 0.7143 | `hold_no_edge` |
| `time_bucket` | `time_1400_close` | 174 | 35 | 0.2965 | -0.6071 | 0.3714 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 313 | 23 | 0.3072 | -1.1957 | 0.3044 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 71, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1087 | 1087 | -0.3744 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1031 | 847 | -0.4393 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 808 | 808 | -0.4583 | `keep_collecting` |
| `latency_state` | `simulated` | 808 | 808 | -0.4583 | `keep_collecting` |
| `actual_order_submitted` | `true` | 897 | 808 | -0.4583 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 769 | 769 | -0.4792 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 671 | 671 | -0.4189 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 674 | 665 | -0.4688 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 529 | 529 | -0.6306 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 545 | 519 | -0.6052 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 519 | 519 | -0.6052 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 446 | 446 | -0.5204 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 419 | 419 | -0.4042 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 398 | 398 | -0.4323 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 370 | 370 | -0.4441 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 347 | 347 | -0.5732 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 321 | 321 | -0.4343 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 289 | 289 | -0.1944 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 265 | 265 | -0.5246 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 247 | 247 | -0.1705 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 143 | 143 | -0.1346 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 137 | 137 | -0.6508 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 133 | 133 | -0.294 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 132 | 132 | -0.5222 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 94 | 94 | -0.2582 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 72 | 72 | -0.3417 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 40 | 40 | -0.847 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 39 | 39 | -0.0459 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 130 | 39 | -0.0459 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 39 | 39 | -0.0459 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 35 | 35 | -0.0234 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 24 | 24 | -2.4602 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -0.8843 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 10 | 10 | -1.9472 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | 0.2339 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -0.6715 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 4 | 4 | -0.2428 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 3 | 3 | -0.0727 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 3 | 3 | -4.0909 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0727 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 808 | 808 | -0.9171 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 808 | 808 | -0.9171 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 613 | 595 | -1.4235 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 418 | 418 | -0.9775 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 335 | 335 | -0.8598 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 301 | 301 | -1.571 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 248 | 248 | -1.2856 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 75 | 73 | 0.205 | `hold_no_edge` |
| `holding_action` | `BUY` | 55 | 55 | -0.8077 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 57 | 53 | 0.1473 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 47 | 46 | 0.5481 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 46 | 46 | -1.2018 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 40 | 40 | 0.015 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 32 | 32 | 0.3902 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 31 | 31 | 0.1865 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 32 | 29 | 2.1286 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 27 | 27 | 0.516 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 22 | 22 | 0.092 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 15 | 15 | 2.9867 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 14 | 14 | 0.3592 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.3157 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 11 | 11 | 1.2909 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.3671 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.2501 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 0.9097 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 40 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 17 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 23 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 40 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1126 | 1126 | -1.33 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 768 | 768 | -0.9362 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 681 | 681 | -1.0643 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 681 | 681 | -1.0643 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 681 | 681 | -1.0643 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 538 | 538 | -1.2387 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 303 | 303 | -0.4717 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 296 | 296 | -1.2276 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 281 | 281 | -1.5412 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 243 | 243 | -1.8074 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 193 | 193 | 0.5093 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 184 | 184 | -0.7774 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 145 | 145 | -0.5187 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 129 | 129 | -0.5497 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 114 | 114 | -0.8361 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 109 | 109 | -1.1905 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 99 | 99 | -2.5306 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 97 | 97 | -1.7109 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 85 | 85 | -1.2013 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 80 | 80 | -0.1602 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 74 | 74 | 0.2094 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 65 | 65 | 0.1757 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 47 | 47 | 0.567 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 849 | 40 | -0.1602 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 35 | 35 | -0.4071 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 35 | 35 | -1.6831 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 32 | 32 | 2.1587 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 31 | 31 | -0.3741 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 20 | 20 | 0.6001 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 20 | 20 | 0.8586 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 19 | 19 | 0.4109 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 18 | 18 | -0.8371 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 18 | 18 | 1.0768 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 17 | 17 | -0.0279 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 16 | 16 | -0.2933 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -0.4952 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 14 | 14 | -0.2816 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 13 | 13 | 0.9109 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 12 | 12 | -0.2982 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 12 | 12 | 2.7475 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 319, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 66599 | 66593 | -0.7837 | -0.8696 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 52384 | 52384 | -0.3634 | -0.4465 | 0.2504 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 26764 | 26764 | 0.6786 | 0.5972 | 0.9802 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_70p` | 26567 | 26567 | -0.3498 | -0.439 | 0.2515 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 11988 | 11988 | 0.6622 | 0.576 | 0.9848 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 11660 | 11660 | -0.3301 | -0.4148 | 0.2648 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 11411 | 11411 | -0.3541 | -0.4259 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 6745 | 6745 | -0.4448 | -0.5088 | 0.2648 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 5239 | 5239 | -0.2739 | -0.2932 | 0.1945 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 4053 | 4053 | -0.365 | -0.4388 | 0.2159 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 3359 | 3359 | -0.4215 | -0.5014 | 0.2045 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1007 | 1007 | -0.4283 | -0.4542 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 771 | 771 | -0.9429 | -0.9429 | 0.0778 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 730 | 730 | -0.8515 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 670 | 670 | -1.0345 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 644 | 644 | -0.7175 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 626 | 626 | -0.6536 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 610 | 610 | -1.2551 | -1.37 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 597 | 597 | -0.9239 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 555 | 555 | -1.2595 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 507 | 507 | -1.0176 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 454 | 454 | -1.9299 | -2.4138 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 404 | 404 | -0.8595 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 355 | 355 | -1.0983 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 348 | 348 | -0.6528 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 342 | 342 | -0.7868 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 325 | 325 | -0.9331 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 298 | 298 | -0.8448 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 295 | 295 | -0.6726 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 290 | 290 | -0.0397 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 275 | 275 | -0.4787 | -0.5298 | 0.1127 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 272 | 272 | -0.9189 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 265 | 265 | -0.7141 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 264 | 264 | -0.6897 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 262 | 262 | -1.1713 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 260 | 260 | -0.7317 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 257 | 257 | -0.9548 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.02)` | 255 | 255 | -0.9306 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 254 | 254 | -1.0199 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 249 | 249 | -0.9614 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 120 | 80 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 80 | 40 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 40 | 40 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 80 | 40 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 80 | 40 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 40 | 40 | -0.1602 | -0.2135 | 0.225 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 62 | 31 | -0.6039 | -0.8051 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 46 | 23 | 0.0134 | 0.0178 | 0.2609 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 18 | 18 | -0.8371 | -1.1161 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 36 | 18 | -0.8371 | -1.1161 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 34 | 17 | -0.3948 | -0.5265 | 0.1765 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 12 | 12 | -0.2982 | -0.3975 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.2982 | -0.3975 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 4 | 4 | 0.2119 | 0.2825 | 0.75 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 4 | 0.2119 | 0.2825 | 0.75 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 6 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.3075 | 0.41 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.7725 | 1.03 | 1.0 | `hold_sample` |

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
