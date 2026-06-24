# Lifecycle Decision Matrix - 2026-06-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-24_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `231858`
- source_rows_total: `341429`
- retained_rows: `231858`
- dropped_rows_by_source: `{}`
- joined_rows: `206843`
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
- lifecycle_flow_bucket_count: `951`
- lifecycle_flow_complete_count: `1201`
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
| `entry` | 13310 | 1831 | 0.7202 | 0.9559 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4629 | 3036 | -0.5098 | 0.9981 | `pass` | `NO_CHANGE` | False |
| `holding` | 4372 | 3036 | -0.9428 | 0.9979 | `pass` | `EXIT` | False |
| `scale_in` | 195730 | 193435 | -0.4341 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 13817 | 5505 | -0.9418 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 951, 'complete_flow_count': 1201, 'incomplete_flow_count': 209335, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 151491 | 150785 | -0.7294 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 41850 | 40261 | 0.6933 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1972 | 1972 | -1.0451 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 422 | 422 | 1.5059 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 339 | 339 | 1.6594 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 218 | 218 | 1.6363 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 174 | 174 | -0.2053 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 64 | 64 | -0.9353 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 38 | 38 | -0.8637 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 28 | 28 | -1.0459 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 23 | 23 | -2.0042 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 15 | 15 | -0.8227 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 15 | 15 | -0.5468 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 15 | 15 | -0.9207 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 13 | 13 | -1.3301 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 13 | 13 | -1.0217 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 13 | 13 | -0.2821 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 546, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 9083 | 1822 | 0.7206 | 0.7925 | 0.4616 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 8713 | 1375 | 0.5891 | 0.265 | 0.4393 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 986 | 986 | 1.5841 | 2.5295 | 0.6481 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 12465 | 986 | 1.5841 | 2.5295 | 0.6481 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 9476 | 771 | -0.2774 | -1.2727 | 0.2386 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 739 | 739 | 1.3172 | 2.1288 | 0.6252 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 5877 | 674 | -0.2859 | -1.3074 | 0.23 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2704 | 662 | 1.2778 | 2.0666 | 0.6314 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 5973 | 637 | 0.0052 | -0.7603 | 0.292 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1317 | 610 | 1.0945 | 1.661 | 0.5853 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5448 | 590 | -0.2806 | -1.2487 | 0.239 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 2888 | 501 | 0.6624 | 0.7148 | 0.487 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1257 | 454 | 0.9567 | 1.4996 | 0.5683 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 5906 | 404 | -0.3022 | -1.4135 | 0.2079 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 402 | 402 | -0.2082 | -1.9812 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2239 | 358 | 0.5257 | 0.3665 | 0.4218 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 552 | 284 | 1.2825 | 1.9185 | 0.588 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1288 | 231 | 0.9834 | 1.4751 | 0.5152 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 969 | 221 | 0.7779 | 1.1079 | 0.4977 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 214 | 214 | -0.2646 | -2.9949 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 197 | 197 | -0.5151 | 2.0192 | 1.0 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 1608 | 186 | -0.0545 | -0.3715 | 0.328 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 111 | 111 | 1.0402 | 1.3746 | 0.6306 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 188, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4485 | 3036 | -0.5098 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 4102 | 3036 | -0.5098 | `keep_collecting` |
| `latency_state` | `simulated` | 4102 | 3036 | -0.5098 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4468 | 3036 | -0.5098 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4054 | 3002 | -0.4967 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3816 | 2839 | -0.5273 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3482 | 2570 | -0.5159 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3339 | 2451 | -0.5516 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2485 | 1843 | -0.5416 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2282 | 1729 | -0.658 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2133 | 1729 | -0.658 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2133 | 1729 | -0.658 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2121 | 1534 | -0.4027 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2011 | 1526 | -0.6648 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1759 | 1359 | -0.612 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1934 | 1304 | -0.3136 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1934 | 1304 | -0.3136 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1784 | 1301 | -0.3685 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1625 | 1090 | -0.2894 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1213 | 904 | -0.5349 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1124 | 794 | -0.3624 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 743 | 551 | -0.2525 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 772 | 466 | -0.476 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 361 | 285 | -0.657 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 362 | 218 | -0.0532 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 759 | 200 | -0.258 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 286 | 197 | -0.2568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 286 | 197 | -0.2568 | `keep_collecting` |
| `would_limit_fill` | `false` | 812 | 196 | -0.2584 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 53, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 4101 | 3036 | -0.9428 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4101 | 3036 | -0.9428 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2370 | 2269 | -1.4447 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2076 | 1549 | -1.0257 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1819 | 1318 | -0.8248 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1161 | 1161 | -1.5031 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 963 | 963 | -1.3747 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 253 | 232 | 0.2301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 210 | 198 | 0.6188 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 206 | 169 | -1.1015 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 214 | 154 | 0.0279 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 145 | 145 | -1.442 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 129 | 122 | 2.1184 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 106 | 106 | 0.3551 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 94 | 94 | 0.7211 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 62 | 62 | 2.3474 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 131 | 61 | -0.3736 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 57 | 57 | 0.0026 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 53 | 53 | 1.9487 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 36 | 36 | -0.4022 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.3744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 271 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 72 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 194 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1065 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 271 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 501 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 527 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 81, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 4091 | 4091 | -1.334 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2874 | 2874 | -1.0042 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2360 | 2360 | -0.9611 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2360 | 2360 | -0.9611 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2360 | 2360 | -0.9611 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1755 | 1755 | -1.199 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1274 | 1274 | -1.2809 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1107 | 1107 | -1.5068 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1027 | 1027 | -0.516 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 878 | 878 | -1.8015 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 740 | 740 | -0.9301 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 621 | 621 | 0.5902 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 591 | 591 | -0.5024 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 517 | 517 | -0.5319 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 462 | 462 | -1.7139 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 425 | 425 | -1.1771 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 387 | 387 | -1.26 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 387 | 387 | -0.8778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 347 | 347 | -2.4555 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 8583 | 271 | -0.1109 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 271 | 271 | -0.1109 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 271 | 271 | -0.1109 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 248 | 248 | 0.2672 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 224 | 224 | 0.0648 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 215 | 215 | 0.7447 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 144 | 144 | -1.681 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 136 | 136 | 2.4202 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 101 | 101 | -0.9607 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 91 | 91 | -0.3501 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 87 | 87 | 0.0876 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 77 | 77 | 1.2031 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 69 | 69 | -0.2923 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 61 | 61 | 0.3194 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 57 | 57 | 0.7889 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 56 | 56 | 2.5073 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 48 | 48 | 0.2667 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 48 | 48 | 0.9753 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 947, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 193393 | 193393 | None | -0.5013 | 0.2041 | `hold_sample` |
| `arm` | `AVG_DOWN` | 153677 | 152971 | None | -0.8011 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 109481 | 109481 | None | -0.5018 | 0.2026 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 107326 | 106620 | None | -0.9657 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 46351 | 46351 | None | -0.4224 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 42053 | 40464 | None | 0.6334 | 0.9766 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 42053 | 40464 | None | 0.6334 | 0.9766 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 36037 | 36037 | None | -0.4705 | 0.2139 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 34044 | 34044 | None | 0.5149 | 0.9806 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 25382 | 25382 | None | -0.5157 | 0.2069 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 19009 | 19009 | None | -0.3277 | 0.1597 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 12468 | 12468 | None | -0.5093 | 0.1921 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10025 | 10025 | None | -0.5599 | 0.1939 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4316 | 4316 | None | -0.4594 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2744 | 2744 | None | -0.8393 | 0.0897 | `hold_sample` |
| `blocker_reason` | `ok` | 1753 | 1753 | None | -2.4031 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1513 | 1513 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1509 | 1509 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1463 | 1463 | None | 3.2288 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1352 | 1352 | None | -1.1 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 542 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 271 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 542 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 271 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 542 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 271 | 271 | -0.1109 | -0.1479 | 0.3395 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 534 | 267 | -0.11 | -0.1467 | 0.3446 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 388 | 194 | -0.0394 | -0.0525 | 0.3711 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 358 | 179 | -0.6572 | -0.8762 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 101 | 101 | -0.9607 | -1.2809 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 202 | 101 | -0.9607 | -1.2809 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 144 | 72 | -0.2744 | -0.3658 | 0.2778 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 70 | 70 | -0.2892 | -0.3856 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 140 | 70 | -0.2892 | -0.3856 | 0.0 | `hold_no_edge` |
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
