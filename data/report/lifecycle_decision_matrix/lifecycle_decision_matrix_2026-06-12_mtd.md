# Lifecycle Decision Matrix - 2026-06-12

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-12_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `122969`
- source_rows_total: `192735`
- retained_rows: `122969`
- dropped_rows_by_source: `{}`
- joined_rows: `113414`
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
- lifecycle_flow_bucket_count: `569`
- lifecycle_flow_complete_count: `579`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0052`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5209 | 901 | 0.393 | 0.9639 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 2746 | 1911 | -0.5891 | 0.997 | `pass` | `NO_CHANGE` | False |
| `holding` | 2588 | 1911 | -0.9652 | 0.9966 | `pass` | `EXIT` | False |
| `scale_in` | 106173 | 105314 | -0.4165 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6253 | 3377 | -0.9841 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 569, 'complete_flow_count': 579, 'incomplete_flow_count': 111595, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 80137 | 79821 | -0.7414 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 24671 | 24128 | 0.6822 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1147 | 1147 | -1.093 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 183 | 183 | 1.3108 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 133 | 133 | 1.3106 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 124 | 124 | 1.0774 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 98 | 98 | -0.3721 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 34 | 34 | -0.9123 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 22 | 22 | -0.9105 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 20 | 20 | -0.8595 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -1.1989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 7 | 7 | -1.7184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 7 | 7 | -0.6166 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 7 | 7 | -0.3182 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 374, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3128 | 899 | 0.3956 | 0.4438 | 0.4438 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 2731 | 611 | 0.3772 | -0.0012 | 0.4255 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 440 | 440 | 1.245 | 2.1599 | 0.6364 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 4748 | 440 | 1.245 | 2.1599 | 0.6364 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 3210 | 438 | -0.4147 | -1.2569 | 0.2443 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1643 | 374 | -0.4251 | -1.2793 | 0.246 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1843 | 374 | -0.2326 | -0.9536 | 0.2888 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 1950 | 373 | -0.4251 | -1.2856 | 0.244 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1501 | 326 | 0.7711 | 1.4404 | 0.6074 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 326 | 326 | 0.7711 | 1.4404 | 0.6074 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1302 | 304 | 0.2358 | 0.1319 | 0.4605 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 495 | 288 | 0.6652 | 1.2023 | 0.5729 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 1979 | 240 | -0.4598 | -1.2252 | 0.2375 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 216 | 216 | -0.3477 | -1.9931 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1017 | 177 | 0.3199 | 0.2005 | 0.4237 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 960 | 154 | -0.0149 | -0.0803 | 0.3701 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 389 | 138 | 0.0694 | 1.6689 | 0.5072 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 374 | 138 | 0.5431 | 0.8231 | 0.5 | `source_quality_workorder` |
| `score_band` | `score_70p` | 294 | 138 | 0.4178 | 0.9781 | 0.558 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 544 | 128 | 0.704 | 0.7222 | 0.4453 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 116 | 116 | -0.7011 | 1.7825 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 59 | 59 | 0.7906 | 1.1097 | 0.6271 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 97, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 2650 | 1911 | -0.5891 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2447 | 1911 | -0.5891 | `keep_collecting` |
| `latency_state` | `simulated` | 2447 | 1911 | -0.5891 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 2642 | 1911 | -0.5891 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2409 | 1883 | -0.5727 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2253 | 1774 | -0.615 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1980 | 1565 | -0.6114 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1965 | 1538 | -0.644 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1641 | 1264 | -0.6833 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1445 | 1152 | -0.7038 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1367 | 1152 | -0.7038 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1367 | 1152 | -0.7038 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1449 | 1132 | -0.6144 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1399 | 1110 | -0.6405 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1048 | 759 | -0.4149 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1048 | 759 | -0.4149 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 834 | 667 | -0.4976 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 806 | 658 | -0.584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 784 | 655 | -0.7617 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 836 | 608 | -0.3991 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 598 | 502 | -0.4485 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 570 | 419 | -0.4115 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 467 | 346 | -0.4881 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 464 | 345 | -0.2548 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 270 | 232 | -0.6135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 243 | 174 | -0.4172 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 185 | 163 | -0.3062 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 194 | 137 | -0.253 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 525 | 137 | -0.253 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 194 | 137 | -0.253 | `keep_collecting` |
| `would_limit_fill` | `false` | 492 | 136 | -0.2553 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 173 | 121 | -0.0888 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 162 | 111 | -0.886 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 45 | 39 | -2.0609 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 37 | 30 | -0.7436 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 38 | 28 | -1.6902 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 38 | 28 | -1.6902 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 19 | 16 | -0.7283 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 20 | 15 | -1.5985 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 18 | 14 | -2.6878 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2447 | 1911 | -0.9652 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2447 | 1911 | -0.9652 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1474 | 1416 | -1.4673 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1671 | 1266 | -1.0546 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 954 | 954 | -1.5222 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 623 | 520 | -0.7158 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 355 | 355 | -1.3294 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 174 | 161 | 0.1947 | `hold_sample` |
| `holding_action` | `BUY` | 153 | 125 | -1.0978 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 129 | 123 | 0.51 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 139 | 112 | 0.0299 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 107 | 107 | -1.4358 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 106 | 106 | 0.0852 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 79 | 79 | -0.009 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 77 | 73 | 1.9949 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 72 | 72 | 0.3972 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 53 | 53 | 0.3898 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 41 | 41 | 0.6392 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 40 | 40 | 2.1385 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 32 | 32 | 0.0874 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 28 | 28 | 1.9477 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 59 | 26 | -0.38 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 15 | 15 | -0.3601 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.4071 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.111 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 141 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 52 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 89 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 536 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 141 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 103 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 405 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 21 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 73, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2534 | 2534 | -1.3608 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1885 | 1885 | -1.0126 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1041 | 1041 | -1.2253 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 818 | 818 | -1.3368 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 729 | 729 | -1.5059 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 690 | 690 | -0.555 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 544 | 544 | -1.8017 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 466 | 466 | -0.9184 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 440 | 440 | 0.4571 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 317 | 317 | -0.5139 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 305 | 305 | -1.7548 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 279 | 279 | -0.5406 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 260 | 260 | -0.9306 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 253 | 253 | -1.2503 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 245 | 245 | -1.3005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 217 | 217 | -2.3955 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 166 | 166 | 0.19 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 154 | 154 | 0.0439 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3017 | 141 | -0.1806 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 141 | 141 | -0.1806 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 141 | 141 | -0.1806 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 129 | 129 | 0.6182 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 82 | 82 | -1.7283 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 77 | 77 | 2.203 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 77 | 77 | -0.5204 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 61 | 61 | -0.4568 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 58 | 58 | -1.0315 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 51 | 51 | -0.0277 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 50 | 50 | 1.016 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 45 | 45 | 0.2807 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 43 | 43 | 0.7867 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 41 | 41 | -0.5096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 36 | 36 | 0.4157 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 34 | 34 | 2.2361 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 33 | 33 | -0.3125 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 33 | 33 | -0.4546 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 28 | 28 | 1.0969 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 562, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 105303 | 105303 | None | -0.4935 | 0.2255 | `hold_sample` |
| `arm` | `AVG_DOWN` | 81397 | 81081 | None | -0.8248 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 57559 | 57243 | None | -0.9926 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 52688 | 52688 | None | -0.4991 | 0.2247 | `hold_sample` |
| `arm` | `PYRAMID` | 24776 | 24233 | None | 0.6157 | 0.9802 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 24776 | 24233 | None | 0.6157 | 0.9802 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 23838 | 23838 | None | -0.4218 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 21249 | 21249 | None | 0.534 | 0.9822 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 21025 | 21025 | None | -0.4319 | 0.2478 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 17669 | 17669 | None | -0.5107 | 0.2215 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 7953 | 7953 | None | -0.5189 | 0.1993 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 7818 | 7818 | None | -0.3008 | 0.201 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 5968 | 5968 | None | -0.5757 | 0.2011 | `hold_sample` |
| `blocker_reason` | `low_broken` | 2450 | 2450 | None | -0.4544 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1552 | 1552 | None | -0.876 | 0.0825 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1077 | 1077 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1075 | 1075 | None | -2.3761 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1007 | 1007 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 928 | 928 | None | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 885 | 885 | None | -0.82 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 282 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 141 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 282 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 141 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 282 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 282 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 141 | 141 | -0.1806 | -0.2408 | 0.3333 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 188 | 94 | -0.7477 | -0.9969 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 178 | 89 | -0.1492 | -0.1989 | 0.3483 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 58 | 58 | -1.0315 | -1.3754 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 116 | 58 | -1.0315 | -1.3754 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 104 | 52 | -0.2345 | -0.3127 | 0.3077 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 33 | 33 | -0.3125 | -0.4167 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 66 | 33 | -0.3125 | -0.4167 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 27 | 27 | 0.273 | 0.3641 | 0.8889 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 54 | 27 | 0.273 | 0.3641 | 0.8889 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 48 | 24 | 0.3131 | 0.4175 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 13 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |

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
