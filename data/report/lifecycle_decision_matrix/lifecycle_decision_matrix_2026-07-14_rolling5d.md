# Lifecycle Decision Matrix - 2026-07-14

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-14_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2774`
- source_rows_total: `4790`
- retained_rows: `2774`
- dropped_rows_by_source: `{}`
- joined_rows: `1414`
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
- lifecycle_flow_bucket_count: `97`
- lifecycle_flow_complete_count: `31`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0153`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 785 | 15 | -0.2359 | 0.0195 | `pass` | `NO_CHANGE` | False |
| `submit` | 162 | 17 | -0.6453 | 0.1257 | `pass` | `NO_CHANGE` | False |
| `holding` | 78 | 17 | -1.0833 | 0.32 | `pass` | `EXIT` | False |
| `scale_in` | 1357 | 1315 | -0.7705 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 392 | 50 | -1.0149 | 0.6782 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 97, 'complete_flow_count': 31, 'incomplete_flow_count': 1991, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1214 | 1179 | -0.8979 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 129 | 122 | 0.4981 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 3 | 3 | -1.2733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 3 | 3 | 0.4867 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 3 | 3 | -1.06 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 2 | 2 | -1.09 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:0b49021de5` | 1 | 1 | 1.4487 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 1 | 1 | -1.46 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8153 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:36ac2952b0` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 1 | 1 | -0.5978 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8ecbdae156` | 1 | 1 | 0.2236 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce1fde0c73` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8880885eab` | 1 | 1 | -1.18 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:48ff71b3f6` | 1 | 1 | -1.1279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:909c6a2905` | 1 | 1 | -3.6197 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:cd91d32ec0` | 1 | 1 | -1.5739 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 183, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 587 | 12 | -0.4166 | -1.0058 | 0.5 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 362 | 9 | 0.0905 | -0.6279 | 0.5555 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 374 | 8 | 0.1843 | -0.0789 | 0.625 | `hold_sample` |
| `score_band` | `score_70p` | 99 | 8 | -0.1991 | -0.6077 | 0.75 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 386 | 7 | -0.5362 | 1.0355 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 247 | 7 | 0.161 | -0.0431 | 0.7143 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 469 | 6 | -0.1077 | -1.1784 | 0.3333 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 369 | 6 | -0.7255 | -0.8333 | 0.6667 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 336 | 6 | -0.7255 | -0.8333 | 0.6667 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | -0.7119 | 1.0467 | 1.0 | `hold_sample` |
| `stale_bucket` | `stale_high` | 258 | 6 | -0.2683 | -1.9017 | 0.3333 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 244 | 6 | -0.1212 | -3.0583 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 256 | 5 | -0.6554 | -0.5204 | 0.8 | `hold_sample` |
| `score_band` | `score_60_62` | 202 | 5 | -0.1554 | -0.8 | 0.4 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 157 | 5 | -0.1421 | -1.432 | 0.4 | `hold_sample` |
| `stale_bucket` | `stale_watch` | 54 | 4 | -0.4517 | -1.2775 | 0.5 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 15 | 3 | -0.1326 | -0.6033 | 0.6667 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 773 | 3 | 0.4867 | 0.4728 | 1.0 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 36 | 3 | 0.4867 | 0.4728 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | 0.0445 | -2.82 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 111, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 138 | 17 | -0.6453 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 149 | 17 | -0.6453 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 75 | 17 | -0.6453 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 75 | 17 | -0.6453 | `keep_collecting` |
| `latency_state` | `simulated` | 75 | 17 | -0.6453 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 138 | 17 | -0.6453 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 75 | 17 | -0.6453 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 72 | 15 | -0.677 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 50 | 13 | -0.4823 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 69 | 13 | -0.2491 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 49 | 13 | -0.4823 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 110 | 13 | -0.4823 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 49 | 13 | -0.4823 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 50 | 13 | -0.4823 | `keep_collecting` |
| `would_limit_fill` | `false` | 118 | 9 | -0.3033 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 30 | 8 | -0.1787 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 25 | 4 | -1.1751 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 25 | 4 | -1.1751 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 6 | 4 | -1.9329 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 25 | 4 | -1.1751 | `keep_collecting` |
| `would_limit_fill` | `true` | 18 | 4 | -0.8847 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 25 | 4 | -1.1751 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 26 | 4 | -1.1751 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 23 | 3 | -1.6901 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -1.87 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 2 | 0.1007 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 19 | 2 | -1.1894 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 1 | -1.3004 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | 0.4859 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 11 | 1 | 0.3699 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -1.3004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -2.6915 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | 0.3699 | `source_quality_workorder` |
| `latency_state` | `caution` | 9 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 9 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 24, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 75 | 17 | -1.0833 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 75 | 17 | -1.0833 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 74 | 16 | -1.1795 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 11 | 10 | -1.8018 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -1.8018 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.36 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | -0.5638 | `candidate_tighten_or_exclude` |
| `holding_action` | `DROP` | 1 | 1 | 0.4555 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.4487 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.4487 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 58 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 58 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 32 | 32 | -1.3875 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 22 | 22 | -1.2136 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 16 | 16 | -1.0716 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.5404 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6222 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -0.0569 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 6 | 6 | -0.7592 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 5 | 5 | -1.6238 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -0.8943 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | -0.36 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -1.7762 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3 | 3 | -0.4325 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 3 | 3 | -1.4157 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.4325 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.4325 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.9442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.748 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.5242 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.5016 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.3362 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.4487 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 1 | 1 | -3.6197 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -3.6197 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.1242 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 1.4487 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 342 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 342 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 74 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 74 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 268 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 268 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 74 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 271, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1355 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `qty_reason` | `qty_none` | 1317 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1275 | 1269 | None | -0.9599 | 0.0685 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1228 | 1193 | None | -1.0626 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1219 | 1184 | None | -1.047 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1062 | 1062 | None | -1.0381 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 745 | 745 | None | -1.4605 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 603 | 603 | None | -1.0218 | 0.0812 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 513 | 513 | None | -0.986 | 0.1111 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 473 | 473 | None | -0.7756 | 0.0951 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 433 | 433 | None | -0.4132 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 399 | 399 | None | -0.8166 | 0.1103 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 269 | 269 | None | -0.9771 | 0.0483 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 223 | 223 | None | -0.6249 | 0.4081 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 224 | 218 | None | -0.9488 | 0.1101 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 130 | 130 | None | -0.8642 | 0.0462 | `hold_sample` |
| `arm` | `PYRAMID` | 129 | 122 | None | 0.4949 | 0.9917 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 129 | 122 | None | 0.4949 | 0.9917 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 21, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `stage` | `exit` | 3 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 3 | 0 | None | None | None | `hold_sample` |

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
