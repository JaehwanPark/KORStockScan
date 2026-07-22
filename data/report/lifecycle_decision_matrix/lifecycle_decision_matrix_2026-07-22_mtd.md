# Lifecycle Decision Matrix - 2026-07-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-22_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `37250`
- source_rows_total: `62709`
- retained_rows: `37250`
- dropped_rows_by_source: `{}`
- joined_rows: `17859`
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
- lifecycle_flow_bucket_count: `320`
- lifecycle_flow_complete_count: `152`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0046`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3809 | 140 | 0.771 | 0.1134 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1150 | 183 | -0.5456 | 0.4405 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 590 | 183 | -1.1354 | 0.6556 | `pass` | `EXIT` | False |
| `scale_in` | 17065 | 16871 | -0.7317 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14636 | 482 | -0.984 | 0.2818 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 320, 'complete_flow_count': 152, 'incomplete_flow_count': 32919, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14460 | 14301 | -0.953 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2375 | 2340 | 0.6356 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 200 | 200 | -1.0198 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 43 | 43 | 0.8851 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 13 | 13 | 4.4797 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 13 | 13 | 0.2535 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.9509 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 10 | 10 | -0.857 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.308 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.82 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 395, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1755 | 125 | 0.9744 | 0.8315 | 0.448 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1671 | 104 | 0.4606 | -0.2678 | 0.4135 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2676 | 77 | -0.14 | -1.2991 | 0.4026 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 1102 | 70 | 1.6338 | 2.8275 | 0.5857 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3732 | 63 | 1.8844 | 3.1182 | 0.5555 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 413 | 63 | 1.8844 | 3.1182 | 0.5555 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 1.8844 | 3.1182 | 0.5555 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 2128 | 61 | 0.0676 | -1.5085 | 0.3279 | `hold_sample` |
| `score_band` | `score_70p` | 514 | 61 | 0.4727 | 0.6824 | 0.541 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 1225 | 56 | 0.5148 | 0.482 | 0.4643 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1430 | 56 | 0.2007 | -1.2103 | 0.3214 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 310 | 50 | 2.1633 | 3.5002 | 0.6 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 923 | 35 | 1.1243 | 2.245 | 0.5429 | `source_quality_workorder` |
| `stale_bucket` | `stale_high` | 1272 | 34 | -0.1958 | -0.8176 | 0.4412 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | 0.1957 | -3.6042 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 1032 | 33 | -0.0026 | -1.2879 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 658 | 32 | 0.3831 | -1.385 | 0.2812 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 594 | 31 | 0.1197 | -2.319 | 0.2258 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 31 | 31 | -0.5422 | 1.8265 | 1.0 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 1371 | 29 | -0.2589 | -0.4585 | 0.4828 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 140, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 855 | 183 | -0.5456 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 562 | 183 | -0.5456 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 562 | 183 | -0.5456 | `keep_collecting` |
| `latency_state` | `simulated` | 562 | 183 | -0.5456 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 855 | 183 | -0.5456 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 1104 | 182 | -0.5486 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 559 | 180 | -0.4898 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 523 | 167 | -0.6085 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 472 | 137 | -0.5376 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 355 | 107 | -0.2215 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 355 | 107 | -0.2215 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 350 | 106 | -0.2237 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 633 | 106 | -0.2237 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 350 | 106 | -0.2237 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 210 | 77 | -0.9886 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 212 | 77 | -0.9886 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 209 | 76 | -1.0018 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 207 | 76 | -1.0018 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 207 | 76 | -1.0018 | `keep_collecting` |
| `would_limit_fill` | `false` | 772 | 54 | -0.1196 | `keep_collecting` |
| `would_limit_fill` | `true` | 166 | 52 | -0.3318 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 160 | 46 | -1.2485 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 88 | 43 | -0.3376 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 163 | 42 | -0.1391 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 89 | 39 | -1.2279 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 137 | 35 | -0.1416 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 92 | 25 | -0.6661 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 75 | 19 | -0.6246 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 29 | 17 | -0.7236 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 34 | 12 | -0.0715 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 12 | -0.0511 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 252 | 6 | -0.3409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 5 | 0.2108 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 5 | -0.0276 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 5 | 4 | 0.6577 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 562 | 183 | -1.1354 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 562 | 183 | -1.1354 | `hold_no_edge` |
| `holding_action` | `WAIT` | 530 | 169 | -1.2141 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 126 | 115 | -1.9975 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 109 | 109 | -2.0153 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 27 | 25 | -0.0225 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 22 | 22 | 0.6072 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 22 | 22 | -0.0541 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.45 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 24 | 11 | -0.1002 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 14 | 11 | 0.0399 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.0016 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.7036 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 4 | -0.3537 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3537 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 28 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 379 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 361 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 70, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 322 | 322 | -1.4439 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 299 | 299 | -0.9386 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 299 | 299 | -0.9386 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 299 | 299 | -0.9386 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 213 | 213 | -1.1865 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 155 | 155 | -1.1755 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 87 | 87 | -0.4916 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 75 | 75 | -0.5357 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 74 | 74 | -1.9397 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 63 | 63 | -0.8304 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 60 | 60 | -1.5474 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 54 | 54 | 0.4099 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 32 | 32 | -1.1579 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 30 | 30 | -1.5223 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 29 | 29 | -2.4349 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 28 | 28 | 0.0837 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.4082 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.4082 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 13064 | 25 | -0.4365 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 0.5397 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 17 | 17 | 0.0789 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -1.8169 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 14 | 14 | -0.5212 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 12 | 12 | -0.8067 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | -3.8938 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 11 | 11 | -1.0323 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 2.1642 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.1856 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.3769 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -0.8505 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.4244 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 6 | 6 | 0.16 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -3.4922 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.3504 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 5 | 5 | 0.6518 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 484, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 14676 | 14517 | None | -1.0712 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 14524 | 14365 | None | -1.0481 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10442 | 10420 | None | -0.754 | 0.1523 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 7522 | 7504 | None | -1.0015 | 0.087 | `hold_sample` |
| `ai_score_source` | `live` | 4127 | 4127 | None | -1.0093 | 0.1156 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3511 | 3510 | None | -0.7638 | 0.1769 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2883 | 2841 | None | -0.8684 | 0.0944 | `hold_sample` |
| `qty_reason` | `qty_none` | 2843 | 2841 | None | -0.8684 | 0.0944 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2885 | 2841 | None | -0.8684 | 0.0944 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2885 | 2841 | None | -0.8684 | 0.0944 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2744 | 2744 | None | -0.7044 | 0.1735 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2648 | 2648 | None | -1.1112 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 2389 | 2354 | None | 0.5958 | 0.9838 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2389 | 2354 | None | 0.5958 | 0.9838 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2194 | 2194 | None | -0.9401 | 0.0934 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1930 | 1930 | None | 0.4315 | 0.9819 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1769 | 1766 | None | -0.6296 | 0.1967 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1641 | 1641 | None | -1.3728 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1448 | 1448 | None | -0.9588 | 0.1084 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1338 | 1338 | None | -0.6811 | 0.1562 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 33, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 56 | 28 | -0.4082 | -0.5443 | 0.1786 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 28 | 28 | -0.4082 | -0.5443 | 0.1786 | `hold_sample` |
| `stage` | `exit` | 28 | 28 | -0.4082 | -0.5443 | 0.1786 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 56 | 28 | -0.4082 | -0.5443 | 0.1786 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.4082 | -0.5443 | 0.1786 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 54 | 27 | -0.3808 | -0.5078 | 0.1852 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 46 | 23 | -0.584 | -0.7787 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | -0.5025 | -0.67 | 0.25 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 30 | 15 | -0.2405 | -0.3207 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 12 | 12 | -0.1731 | -0.2308 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.1731 | -0.2308 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 11 | -1.0323 | -1.3764 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0207 | -1.361 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 18 | 9 | -0.6742 | -0.8989 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |

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
