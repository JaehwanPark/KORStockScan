# Lifecycle Decision Matrix - 2026-06-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-11_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `88018`
- source_rows_total: `145667`
- retained_rows: `88018`
- dropped_rows_by_source: `{}`
- joined_rows: `82485`
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
- lifecycle_flow_bucket_count: `402`
- lifecycle_flow_complete_count: `425`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3701 | 736 | 0.4103 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1768 | 1495 | -0.5117 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1649 | 1495 | -0.8869 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 76479 | 76130 | -0.3902 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4421 | 2629 | -0.9491 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 402, 'complete_flow_count': 425, 'incomplete_flow_count': 80245, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 55449 | 55321 | -0.7565 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 19824 | 19603 | 0.6712 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1024 | 1024 | -1.0951 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 172 | 172 | 1.3103 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 123 | 123 | 1.2482 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 94 | 94 | -0.3789 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 91 | 91 | 0.7053 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 23 | 23 | -0.8943 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 19 | 19 | -0.8679 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 13 | 13 | -1.0485 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -1.1989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 7 | 7 | -1.7184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 6 | 6 | -1.9202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 6 | 6 | -1.7784 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 6 | 6 | -0.374 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 5 | 5 | -0.9619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 5 | 5 | -1.221 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:84b7dde4a3` | 4 | 4 | -1.5568 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:6564dad233` | 4 | 4 | -1.161 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 314, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2067 | 736 | 0.4103 | 0.5303 | 0.466 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1698 | 480 | 0.4346 | 0.1691 | 0.4521 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 386 | 386 | 1.1479 | 2.0149 | 0.6295 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3351 | 386 | 1.1479 | 2.0149 | 0.6295 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1948 | 328 | -0.3874 | -1.1731 | 0.2683 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1286 | 272 | 0.5391 | 1.0919 | 0.5919 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 272 | 272 | 0.5391 | 1.0919 | 0.5919 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 821 | 265 | -0.3138 | -1.0452 | 0.3019 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 690 | 263 | -0.4046 | -1.181 | 0.2776 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 834 | 262 | -0.4046 | -1.1895 | 0.2748 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 788 | 245 | 0.1991 | 0.1703 | 0.4816 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 329 | 242 | 0.5707 | 1.0714 | 0.5786 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1294 | 171 | -0.4264 | -1.086 | 0.2748 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 158 | 158 | -0.3143 | -1.9795 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 663 | 158 | 0.3981 | 0.229 | 0.4304 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 249 | 125 | 0.344 | 0.919 | 0.552 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 391 | 123 | 0.7066 | 0.6564 | 0.4472 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 286 | 115 | -0.175 | 1.3855 | 0.5391 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 150 | 101 | 0.6018 | 0.8526 | 0.594 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 98 | 98 | -0.6883 | 1.7367 | 1.0 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 231 | 95 | 0.129 | 0.1254 | 0.4421 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 563 | 94 | -0.4016 | -0.5174 | 0.383 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 82 | 82 | -0.2755 | -2.8991 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1400_close` | 258 | 38 | -0.8868 | -1.1281 | 0.3158 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 76, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 2155 | 2058 | -0.4745 | `keep_collecting` |
| `actual_order_submitted` | `false` | 2094 | 1604 | -0.4942 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1559 | 1495 | -0.5117 | `keep_collecting` |
| `latency_state` | `simulated` | 1559 | 1495 | -0.5117 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1766 | 1495 | -0.5117 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1444 | 1386 | -0.5319 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1270 | 1213 | -0.5117 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1272 | 1199 | -0.5648 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1101 | 1058 | -0.6353 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 996 | 954 | -0.5828 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 963 | 932 | -0.5937 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 993 | 908 | -0.5741 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 938 | 908 | -0.5741 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 904 | 861 | -0.5164 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 621 | 587 | -0.4149 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 536 | 521 | -0.5598 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 525 | 506 | -0.5805 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 494 | 466 | -0.3991 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 465 | 448 | -0.3145 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 348 | 326 | -0.3928 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 338 | 323 | -0.201 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 289 | 282 | -0.5112 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 281 | 272 | -0.205 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 195 | 187 | -0.5165 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 134 | 133 | -0.2599 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 133 | 128 | -0.4596 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 115 | 109 | -0.2541 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 324 | 109 | -0.2541 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 115 | 109 | -0.2541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 101 | 95 | -0.0468 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 97 | 92 | -0.7398 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 35 | 35 | -2.1838 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 25 | 24 | -1.3338 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 21 | -0.5878 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 14 | 14 | -1.6608 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 14 | 13 | -0.3691 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 12 | 12 | -2.492 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 9 | 0.1268 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 9 | 8 | 0.0164 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -2.2596 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1559 | 1495 | -0.8869 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1559 | 1495 | -0.8869 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1103 | 1073 | -1.4278 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1106 | 1061 | -0.9987 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 777 | 777 | -1.4954 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 351 | 340 | -0.5296 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 218 | 218 | -1.2292 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 151 | 141 | 0.1594 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 111 | 105 | 0.5477 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 123 | 99 | 0.0162 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 96 | 96 | 0.0287 | `hold_no_edge` |
| `holding_action` | `BUY` | 102 | 94 | -0.9172 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 78 | 78 | -1.3089 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 77 | 77 | -0.0111 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 63 | 63 | 0.4074 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 64 | 61 | 2.1263 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 43 | 43 | 0.4202 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 36 | 36 | 2.1881 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 32 | 32 | 0.7475 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 22 | 22 | 0.1115 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 21 | 21 | 2.1255 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 33 | 16 | -0.3243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 12 | 12 | -0.3342 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.5753 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2943 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 90 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 29 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 61 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 64 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 90 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 45 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 67, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1953 | 1953 | -1.3305 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1337 | 1337 | -0.9382 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1202 | 1202 | -1.0299 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 929 | 929 | -1.2309 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 547 | 547 | -1.2568 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 520 | 520 | -1.446 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 484 | 484 | -0.4608 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 395 | 395 | -1.7914 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 336 | 336 | 0.4928 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 333 | 333 | -0.8391 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 265 | 265 | -0.517 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 244 | 244 | -0.537 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 208 | 208 | -1.6251 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 180 | 180 | -0.0322 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 172 | 172 | -0.8524 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 169 | 169 | -1.2629 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 167 | 167 | -1.2146 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 164 | 164 | -2.3589 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 126 | 126 | 0.1756 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 125 | 125 | 0.0637 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 99 | 99 | 0.6741 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 1882 | 90 | -0.0322 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 62 | 62 | -1.731 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 61 | 61 | 2.3502 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 56 | 56 | -0.435 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 42 | 42 | -0.5122 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 37 | 37 | -0.0302 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 37 | 37 | 1.0375 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 35 | 35 | 0.7144 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 35 | 35 | 0.2474 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 30 | 30 | -1.205 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 29 | 29 | -0.5257 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 29 | 29 | 0.4014 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 27 | 27 | 2.275 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 24 | 24 | 0.2718 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 24 | 24 | 0.0245 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 23 | 23 | -0.4776 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 21 | 21 | 1.207 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 355, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 97067 | 96811 | -0.8288 | -0.9162 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 76125 | 76125 | -0.3903 | -0.471 | 0.2533 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 40486 | 40486 | -0.3973 | -0.4845 | 0.248 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 39846 | 39404 | 0.6702 | 0.6004 | 0.979 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 17593 | 17593 | 0.6205 | 0.5451 | 0.9807 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 16045 | 16045 | -0.3479 | -0.4164 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 13463 | 13463 | -0.3177 | -0.3998 | 0.2886 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 12964 | 12964 | -0.4292 | -0.4887 | 0.2456 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 5104 | 5104 | -0.2594 | -0.2815 | 0.2263 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 4784 | 4784 | -0.418 | -0.4957 | 0.2427 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 4428 | 4428 | -0.4033 | -0.4871 | 0.2285 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1566 | 1566 | -0.4256 | -0.4505 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1370 | 1370 | -0.8795 | -0.8791 | 0.0883 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 873 | 873 | -0.8546 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 871 | 871 | -1.0534 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 840 | 840 | -1.9387 | -2.3845 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 762 | 762 | -1.2536 | -1.37 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 744 | 744 | -0.7206 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 710 | 710 | -0.9223 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 708 | 708 | -1.0105 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 678 | 678 | -0.6585 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 659 | 659 | -1.2671 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 522 | 522 | -0.8611 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 514 | 514 | -1.0908 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 492 | 492 | -0.9636 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 465 | 465 | -0.9364 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 447 | 447 | -0.6441 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 443 | 443 | -0.8053 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 433 | 433 | -0.7504 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 431 | 431 | -0.9323 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 402 | 402 | -0.7814 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 398 | 398 | -1.0319 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 394 | 394 | 2.8808 | 2.9441 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_cutoff` | 390 | 390 | -0.1845 | -0.239 | 0.3436 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 376 | 376 | -0.667 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 362 | 362 | -0.7221 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 361 | 361 | -0.8179 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 361 | 361 | -0.8328 | -0.91 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 359 | 359 | -0.6496 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 348 | 348 | -0.8082 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 270 | 180 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 180 | 90 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 90 | 90 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 180 | 90 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 180 | 90 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 90 | 90 | -0.0322 | -0.0429 | 0.4445 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 122 | 61 | -0.0172 | -0.023 | 0.459 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 100 | 50 | -0.8309 | -1.1078 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 30 | 30 | -1.205 | -1.6067 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 60 | 30 | -1.205 | -1.6067 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 58 | 29 | -0.0636 | -0.0848 | 0.4138 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 24 | 24 | 0.2718 | 0.3625 | 0.875 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 48 | 24 | 0.2718 | 0.3625 | 0.875 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 42 | 21 | 0.3175 | 0.4233 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 17 | 17 | -0.3088 | -0.4118 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 34 | 17 | -0.3088 | -0.4118 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 10 | 10 | 0.8265 | 1.102 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 20 | 10 | 0.8265 | 1.102 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 20 | 10 | 0.8265 | 1.102 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 6 | 6 | 1.4287 | 1.905 | 1.0 | `hold_sample` |

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
