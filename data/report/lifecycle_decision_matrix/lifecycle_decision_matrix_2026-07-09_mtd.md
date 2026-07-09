# Lifecycle Decision Matrix - 2026-07-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-09_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `31032`
- source_rows_total: `49418`
- retained_rows: `31032`
- dropped_rows_by_source: `{}`
- joined_rows: `14800`
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
- lifecycle_flow_bucket_count: `233`
- lifecycle_flow_complete_count: `84`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0029`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1780 | 112 | 0.991 | 0.1377 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 681 | 146 | -0.6275 | 0.523 | `pass` | `NO_CHANGE` | False |
| `holding` | 454 | 146 | -1.2221 | 0.7499 | `pass` | `EXIT` | False |
| `scale_in` | 14180 | 14030 | -0.7292 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 13937 | 366 | -1.0297 | 0.1513 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 233, 'complete_flow_count': 84, 'incomplete_flow_count': 28689, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 11866 | 11744 | -0.9679 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2098 | 2070 | 0.6393 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 187 | 187 | -1.02 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 41 | 41 | 0.9124 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 13 | 13 | 4.4797 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 13 | 13 | 0.2535 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.9509 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.308 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.82 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 2 | 2 | -1.6292 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 16 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 2 | 2 | -1.3398 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 15 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 2 | 2 | -1.8977 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 341, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1100 | 105 | 1.1253 | 1.1847 | 0.4571 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 980 | 84 | 0.524 | -0.1346 | 0.4167 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 231 | 64 | 1.8876 | 3.1417 | 0.5781 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1728 | 60 | 1.9748 | 3.2805 | 0.55 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 330 | 60 | 1.9748 | 3.2805 | 0.55 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 60 | 60 | 1.9748 | 3.2805 | 0.55 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 329 | 53 | 0.6259 | 0.8664 | 0.5094 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1025 | 52 | -0.144 | -1.4444 | 0.3846 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 161 | 45 | 2.3857 | 4.0608 | 0.6222 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1145 | 43 | 0.0262 | -1.6475 | 0.3256 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 524 | 43 | 0.6828 | 0.5873 | 0.3954 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 938 | 43 | 0.2485 | -1.0382 | 0.3488 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 440 | 31 | 1.4238 | 2.6088 | 0.5161 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 358 | 27 | 0.0811 | -2.4856 | 0.2222 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 27 | 27 | 0.1656 | -3.6189 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 717 | 24 | 0.0354 | -1.4975 | 0.2917 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 305 | 21 | 0.4763 | -0.9323 | 0.381 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 20 | 20 | -0.4422 | 2.222 | 1.0 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 282 | 19 | -0.1625 | -0.9924 | 0.3158 | `hold_sample` |
| `stale_bucket` | `stale_high` | 711 | 19 | -0.3053 | -0.6053 | 0.4737 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 117, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 468 | 146 | -0.6275 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 434 | 146 | -0.6275 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 434 | 146 | -0.6275 | `keep_collecting` |
| `latency_state` | `simulated` | 434 | 146 | -0.6275 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 468 | 146 | -0.6275 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 677 | 145 | -0.6319 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 431 | 143 | -0.559 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 400 | 133 | -0.6891 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 359 | 109 | -0.6221 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 269 | 80 | -0.2448 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 269 | 80 | -0.2448 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 265 | 79 | -0.248 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 297 | 79 | -0.248 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 265 | 79 | -0.248 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 168 | 67 | -1.075 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 169 | 67 | -1.075 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 167 | 66 | -1.0915 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 165 | 66 | -1.0915 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 165 | 66 | -1.0915 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 120 | 43 | -1.2524 | `keep_collecting` |
| `would_limit_fill` | `true` | 130 | 42 | -0.3032 | `keep_collecting` |
| `would_limit_fill` | `false` | 382 | 37 | -0.1854 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 81 | 36 | -1.231 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 73 | 34 | -0.3569 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 106 | 29 | -0.1954 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 117 | 27 | -0.1847 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 58 | 19 | -0.6319 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 15 | -0.6501 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 24 | 13 | -0.5437 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 30 | 10 | -0.2116 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 10 | -0.1872 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 196 | 5 | -1.233 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 5 | -0.0276 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -0.7665 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 4 | 3 | 0.715 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 434 | 146 | -1.2221 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 434 | 146 | -1.2221 | `hold_no_edge` |
| `holding_action` | `WAIT` | 406 | 135 | -1.3175 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 103 | 93 | -2.1441 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 89 | 89 | -2.1555 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 21 | 21 | 0.5767 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 22 | 20 | 0.0392 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 18 | 18 | 0.4057 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.0091 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 21 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 1.7333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 4 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.7787 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 20 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 288 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 20 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 271 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 58, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 249 | 249 | -1.5229 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 161 | 161 | -1.2204 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 120 | 120 | -1.2888 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 63 | 63 | -1.9894 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 59 | 59 | -0.4979 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 55 | 55 | -0.5196 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 50 | 50 | -1.7396 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 49 | 49 | -0.8162 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 39 | 39 | 0.5426 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 27 | 27 | -1.5318 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 26 | 26 | -2.4916 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 23 | 23 | 0.1604 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 21 | 21 | -1.3185 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 13591 | 20 | -0.4635 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 20 | 20 | -0.4635 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | -0.4635 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 18 | 18 | 0.5003 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 10 | 10 | -3.9212 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 10 | 10 | -1.0402 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.9198 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.6304 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | 0.1114 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 2.2537 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.3769 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 0.554 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.166 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -3.4667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.3258 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -3.6004 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 426, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 12068 | 11946 | None | -1.0817 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 11933 | 11811 | None | -1.0569 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10095 | 10079 | None | -0.7527 | 0.1535 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4761 | 4749 | None | -1.0581 | 0.0944 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3509 | 3508 | None | -0.7648 | 0.1767 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2740 | 2740 | None | -0.706 | 0.1723 | `hold_sample` |
| `ai_score_source` | `live` | 2686 | 2686 | None | -1.0717 | 0.1225 | `hold_sample` |
| `arm` | `PYRAMID` | 2112 | 2084 | None | 0.5955 | 0.9822 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2112 | 2084 | None | 0.5955 | 0.9822 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1751 | 1751 | None | 0.4392 | 0.98 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1710 | 1707 | None | -0.6636 | 0.1783 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1318 | 1318 | None | -0.6911 | 0.1472 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1193 | 1193 | None | -1.0067 | 0.1098 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 455 | 455 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 386 | 386 | None | -0.54 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 345 | 345 | None | -1.586 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 243 | 243 | None | -0.847 | 0.0659 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 199 | 199 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 198 | 198 | None | -0.43 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 193 | 193 | None | -1.7726 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 40 | 20 | -0.4635 | -0.618 | 0.25 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 20 | 20 | -0.4635 | -0.618 | 0.25 | `hold_sample` |
| `stage` | `exit` | 20 | 20 | -0.4635 | -0.618 | 0.25 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 40 | 20 | -0.4635 | -0.618 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | -0.4635 | -0.618 | 0.25 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 38 | 19 | -0.4275 | -0.57 | 0.2632 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 38 | 19 | -0.4788 | -0.6384 | 0.2632 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 30 | 15 | -0.7515 | -1.002 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 24 | 12 | -0.2575 | -0.3433 | 0.4167 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 20 | 10 | -1.0402 | -1.387 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.0283 | -1.3711 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.9195 | -1.226 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |

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
