# Lifecycle Decision Matrix - 2026-07-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-13_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3469`
- source_rows_total: `5073`
- retained_rows: `3469`
- dropped_rows_by_source: `{}`
- joined_rows: `1614`
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
- lifecycle_flow_bucket_count: `106`
- lifecycle_flow_complete_count: `25`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0093`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 797 | 19 | -0.2403 | 0.0181 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 166 | 29 | -0.5484 | 0.242 | `pass` | `NO_CHANGE` | False |
| `holding` | 79 | 29 | -1.1266 | 0.5031 | `pass` | `EXIT` | False |
| `scale_in` | 1528 | 1480 | -0.8018 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 899 | 57 | -1.0263 | 0.4142 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 106, 'complete_flow_count': 25, 'incomplete_flow_count': 2668, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1335 | 1295 | -0.9709 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 167 | 159 | 0.6206 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 22 | 22 | -1.0578 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 3 | 3 | 0.4867 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 2 | 2 | -0.205 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:0b49021de5` | 1 | 1 | 1.4487 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.9899 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9b3d586d84` | 1 | 1 | -1.2667 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3ecc9eeb81` | 1 | 1 | 0.9467 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8cfdf34d0a` | 1 | 1 | -1.38 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.3812 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 1 | 1 | -0.5978 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8ecbdae156` | 1 | 1 | 0.2236 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5e39da79b4` | 1 | 1 | -4.7933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:48ff71b3f6` | 1 | 1 | -1.1279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:909c6a2905` | 1 | 1 | -3.6197 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b19e5449ca` | 1 | 1 | 0.2149 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 181, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 596 | 16 | -0.3766 | -1.08 | 0.5 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 383 | 12 | 0.2553 | -0.3909 | 0.5833 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 372 | 10 | 0.2636 | 0.4179 | 0.7 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 476 | 9 | 0.1781 | -0.6789 | 0.4445 | `hold_sample` |
| `score_band` | `score_70p` | 150 | 9 | -0.5409 | -1.2257 | 0.6667 | `hold_sample` |
| `stale_bucket` | `stale_high` | 263 | 9 | -0.4137 | -1.4189 | 0.4445 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 402 | 8 | -0.8785 | 0.1348 | 0.875 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.3888 | 1.3862 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 237 | 8 | -0.0085 | 0.3598 | 0.75 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 264 | 8 | 0.3395 | -2.5713 | 0.125 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 368 | 7 | -1.0897 | -1.5957 | 0.5714 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 343 | 7 | -1.0897 | -1.5957 | 0.5714 | `hold_sample` |
| `score_band` | `score_60_62` | 206 | 7 | -0.1263 | -0.6672 | 0.4286 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 206 | 7 | 0.3905 | -1.34 | 0.4286 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 260 | 5 | -0.6554 | -0.5204 | 0.8 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 22 | 4 | -0.9182 | -1.995 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 4 | 4 | 0.0566 | -3.435 | 0.0 | `hold_sample` |
| `stale_bucket` | `stale_watch` | 47 | 4 | -0.4517 | -1.2775 | 0.5 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 158 | 4 | -1.8076 | -2.34 | 0.5 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 781 | 3 | 0.4867 | 0.4728 | 1.0 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 135 | 29 | -0.5484 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 157 | 29 | -0.5484 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 75 | 29 | -0.5484 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 75 | 29 | -0.5484 | `keep_collecting` |
| `latency_state` | `simulated` | 75 | 29 | -0.5484 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 135 | 29 | -0.5484 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 74 | 28 | -0.5373 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 71 | 26 | -0.5529 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 67 | 22 | -0.1478 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 49 | 17 | -0.4007 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 49 | 17 | -0.4007 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 108 | 17 | -0.4007 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 49 | 17 | -0.4007 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 49 | 17 | -0.4007 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 26 | 12 | -0.7576 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 25 | 12 | -0.7576 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 26 | 12 | -0.7576 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 26 | 12 | -0.7576 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 26 | 12 | -0.7576 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 122 | 11 | 0.0717 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 30 | 10 | 0.2089 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 20 | 7 | -1.3074 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 7 | 6 | -1.9657 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 6 | -1.0767 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 18 | 6 | -1.2668 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 18 | 5 | 0.0119 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 4 | -1.9506 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | 0.2296 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 2 | -1.0072 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 2 | 0.1007 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | 0.4859 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.8585 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -1.3004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -2.6915 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.8585 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 75 | 29 | -1.1266 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 75 | 29 | -1.1266 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 74 | 28 | -1.1831 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 20 | 18 | -2.0405 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 18 | 18 | -2.0405 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.36 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.5638 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.0838 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 1.1977 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.0838 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.1977 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.6471 | `hold_sample` |
| `holding_action` | `DROP` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 46 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 46 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 34 | 34 | -1.6842 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 27 | 27 | -1.1023 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 26 | 26 | -1.0081 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 26 | 26 | -1.0081 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 26 | 26 | -1.0081 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 16 | 16 | -1.3288 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 11 | 11 | -0.8798 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.5168 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 11 | 11 | -1.9236 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | 0.3688 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 9 | 9 | -0.9441 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.5933 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 7 | 7 | -1.6552 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | -0.235 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -2.1442 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 4 | 4 | -0.6319 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.6319 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.6319 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -1.4157 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.6894 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.7901 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.0838 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 1.1977 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 2 | 2 | -4.2065 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -1.0913 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.748 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.1977 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.5016 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.6471 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.3362 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.39 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -3.6197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -4.7933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1242 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.2149 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 842 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 314, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1379 | 1372 | None | -0.9888 | 0.0809 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1359 | 1319 | None | -1.1408 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1341 | 1301 | None | -1.1124 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1091 | 1091 | None | -1.0852 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1035 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `qty_reason` | `qty_none` | 997 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1037 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1037 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `ai_score_source` | `live` | 786 | 786 | None | -1.1229 | 0.0929 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 536 | 536 | None | -0.9205 | 0.138 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 533 | 533 | None | -1.0561 | 0.0825 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 467 | 467 | None | -1.3686 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 446 | 446 | None | -0.7024 | 0.1031 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 395 | 395 | None | -0.4099 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 287 | 287 | None | -0.6957 | 0.3728 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 275 | 275 | None | -0.884 | 0.1018 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 233 | 226 | None | -0.9213 | 0.1372 | `hold_sample` |
| `arm` | `PYRAMID` | 169 | 161 | None | 0.6091 | 0.9813 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 169 | 161 | None | 0.6091 | 0.9813 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 131 | 131 | None | -0.826 | 0.0764 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.6319 | -0.8425 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.46 | -0.6133 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.785 | -1.0467 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.0913 | -1.455 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.035 | -1.38 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_lt040` | 2 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |

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
