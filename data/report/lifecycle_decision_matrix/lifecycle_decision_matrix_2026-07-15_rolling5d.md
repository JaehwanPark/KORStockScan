# Lifecycle Decision Matrix - 2026-07-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-15_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1151`
- source_rows_total: `2651`
- retained_rows: `1151`
- dropped_rows_by_source: `{}`
- joined_rows: `690`
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
- lifecycle_flow_bucket_count: `58`
- lifecycle_flow_complete_count: `25`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0296`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 295 | 7 | -0.6835 | 0.0269 | `pass` | `NO_CHANGE` | False |
| `submit` | 84 | 10 | -0.621 | 0.1698 | `pass` | `NO_CHANGE` | False |
| `holding` | 39 | 10 | -1.4975 | 0.456 | `pass` | `EXIT` | False |
| `scale_in` | 622 | 621 | -1.1312 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 111 | 42 | -1.1221 | 0.803 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 58, 'complete_flow_count': 25, 'incomplete_flow_count': 819, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 598 | 597 | -1.1606 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 10 | 10 | 0.575 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 3 | 3 | -1.2733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 3 | 3 | -1.06 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 2 | 2 | -1.09 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 1 | 1 | -1.46 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8153 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:36ac2952b0` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce1fde0c73` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8880885eab` | 1 | 1 | -1.18 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:48ff71b3f6` | 1 | 1 | -1.1279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:cd91d32ec0` | 1 | 1 | -1.5739 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:452add0e70` | 1 | 1 | -2.4233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:4605369e6e` | 1 | 1 | -1.5939 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:43a09edbd6` | 1 | 1 | -1.4744 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:7f6445a63b` | 1 | 1 | -2.8982 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 118, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 215 | 7 | -0.6835 | -2.1957 | 0.2857 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 67 | 5 | -0.2305 | -3.35 | 0.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 179 | 4 | -1.1559 | -1.36 | 0.5 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 160 | 4 | -1.1559 | -1.36 | 0.5 | `source_quality_workorder` |
| `stale_bucket` | `stale_high` | 84 | 4 | -0.6229 | -2.4575 | 0.25 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 132 | 3 | -0.0535 | -3.31 | 0.0 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 83 | 3 | -0.0535 | -3.31 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -0.287 | -3.2967 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 31 | 3 | -1.1078 | -2.24 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_watch` | 34 | 3 | -0.7642 | -1.8467 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 29 | 3 | -0.5307 | -1.86 | 0.3333 | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 6 | 2 | -0.4418 | -1.12 | 0.5 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 123 | 2 | -1.87 | -1.6 | 0.5 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 140 | 2 | -1.8157 | 0.69 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 98 | 2 | 0.2497 | -2.455 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.1459 | -3.43 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | -1.8157 | 0.69 | 1.0 | `hold_sample` |
| `score_band` | `score_60_62` | 39 | 2 | -0.1459 | -3.43 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 217 | 2 | -0.5846 | -0.895 | 0.5 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 73 | 2 | 0.274 | -3.295 | 0.0 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 75 | 10 | -0.621 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 78 | 10 | -0.621 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 37 | 10 | -0.621 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 37 | 10 | -0.621 | `keep_collecting` |
| `latency_state` | `simulated` | 37 | 10 | -0.621 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 75 | 10 | -0.621 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 37 | 10 | -0.621 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 36 | 9 | -0.5456 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 24 | 8 | -0.7568 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 23 | 8 | -0.7568 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 60 | 8 | -0.7568 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 23 | 8 | -0.7568 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 24 | 8 | -0.7568 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 33 | 7 | -0.1672 | `keep_collecting` |
| `would_limit_fill` | `false` | 62 | 5 | -0.5462 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 4 | -0.3576 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 3 | -1.6801 | `keep_collecting` |
| `would_limit_fill` | `true` | 8 | 3 | -1.1078 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 13 | 2 | -0.0781 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 13 | 2 | -0.0781 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 13 | 2 | -0.0781 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -1.87 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 13 | 2 | -0.0781 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 14 | 2 | -0.0781 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | -1.3004 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 13 | 1 | -0.5262 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 4 | 1 | 0.3699 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | -1.3004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 1 | 0.4167 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 1 | -0.5262 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.3699 | `source_quality_workorder` |
| `latency_state` | `caution` | 5 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 5 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 38 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 10 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 18, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 37 | 10 | -1.4975 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_not_applicable_at_start` | 37 | 10 | -1.4975 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 37 | 10 | -1.4975 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 9 | 8 | -1.725 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.725 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -1.1279 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.0474 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 31 | 31 | -1.042 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 30 | 30 | -1.3394 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 22 | 22 | -1.2136 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 10 | 10 | -0.5772 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 9 | 9 | -1.5228 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6222 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -1.7762 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -1.47 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | -1.2318 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.9442 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2 | 2 | -0.5625 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.8247 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.5625 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.5625 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | -0.5877 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.5242 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 1 | 1 | -2.8982 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.8982 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0474 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 69 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 69 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 36 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 36 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 33 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 33 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 36 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 33 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 195, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 622 | 621 | None | -1.3582 | 0.0161 | `hold_sample` |
| `qty_reason` | `qty_none` | 621 | 621 | None | -1.3582 | 0.0161 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 622 | 621 | None | -1.3582 | 0.0161 | `hold_sample` |
| `time_bucket` | `time_unknown` | 622 | 621 | None | -1.3582 | 0.0161 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 614 | 614 | None | -1.368 | 0.013 | `hold_sample` |
| `arm` | `AVG_DOWN` | 612 | 611 | None | -1.3898 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 604 | 603 | None | -1.3666 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 489 | 489 | None | -1.4013 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 487 | 487 | None | -1.6283 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 349 | 349 | None | -1.4371 | 0.0114 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 253 | 253 | None | -1.4718 | 0.0197 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 162 | 162 | None | -1.3925 | 0.0062 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 160 | 160 | None | -1.424 | 0.0062 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 133 | 133 | None | -1.2618 | 0.0151 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 129 | 129 | None | -1.2617 | 0.0543 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 119 | 119 | None | -0.4709 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 99 | 99 | None | -1.0094 | 0.0505 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 72 | 72 | None | -1.034 | 0.0278 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 31 | 31 | None | -1.0503 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.48)` | 20 | 20 | None | -0.48 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 20, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 2 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |

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
