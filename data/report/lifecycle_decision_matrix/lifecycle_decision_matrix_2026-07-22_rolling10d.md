# Lifecycle Decision Matrix - 2026-07-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-22_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4596`
- source_rows_total: `11153`
- retained_rows: `4596`
- dropped_rows_by_source: `{}`
- joined_rows: `2336`
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
- lifecycle_flow_bucket_count: `113`
- lifecycle_flow_complete_count: `62`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0199`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1540 | 21 | -0.1664 | 0.0191 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 391 | 30 | -0.1154 | 0.1273 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 97 | 30 | -0.8635 | 0.3202 | `pass` | `EXIT` | False |
| `scale_in` | 2150 | 2147 | -0.8396 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 418 | 108 | -0.8687 | 0.7432 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 113, 'complete_flow_count': 62, 'incomplete_flow_count': 3059, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1978 | 1975 | -0.9601 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 158 | 158 | 0.6891 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 10 | 10 | -0.857 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 2 | 2 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 2 | 2 | -0.835 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8153 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:65653fdfbd` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:36ac2952b0` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b9452e4761` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 191, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1279 | 20 | -0.1536 | -1.411 | 0.35 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 646 | 15 | 0.2322 | -1.6027 | 0.2667 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 377 | 15 | 0.2322 | -1.6027 | 0.2667 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 416 | 15 | 0.2481 | -1.3416 | 0.2667 | `hold_sample` |
| `stale_bucket` | `stale_high` | 387 | 13 | -0.1336 | -1.1323 | 0.3846 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 316 | 13 | 0.0722 | -1.6031 | 0.3077 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 226 | 10 | 0.2185 | -2.2464 | 0.1 | `hold_sample` |
| `score_band` | `score_lt60` | 1246 | 9 | 0.2438 | -1.32 | 0.3333 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 527 | 8 | -0.1383 | -0.5688 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | 0.324 | -2.0386 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -1.0466 | 1.04 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | 0.331 | -3.5383 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 152 | 6 | -0.075 | -1.57 | 0.3333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1076 | 5 | -1.311 | -0.836 | 0.6 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 843 | 5 | -0.8597 | -0.062 | 0.6 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1021 | 5 | -1.311 | -0.836 | 0.6 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 739 | 4 | -1.5233 | -0.761 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 79 | 4 | 0.235 | -1.1775 | 0.25 | `hold_sample` |
| `score_band` | `score_70p` | 118 | 4 | -1.3137 | -1.365 | 0.5 | `hold_sample` |
| `stale_bucket` | `stale_watch` | 162 | 4 | -1.056 | -1.07 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 116, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 324 | 30 | -0.1154 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 356 | 30 | -0.1154 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 90 | 30 | -0.1154 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 90 | 30 | -0.1154 | `keep_collecting` |
| `latency_state` | `simulated` | 90 | 30 | -0.1154 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 324 | 30 | -0.1154 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 90 | 30 | -0.1154 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 87 | 28 | -0.1685 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 60 | 22 | -0.1775 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 77 | 22 | -0.1713 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 59 | 22 | -0.1775 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 286 | 22 | -0.1775 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 59 | 22 | -0.1775 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 60 | 22 | -0.1775 | `keep_collecting` |
| `would_limit_fill` | `false` | 334 | 13 | 0.0309 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 30 | 11 | -0.0779 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 26 | 9 | -0.4785 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 30 | 8 | 0.0556 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 30 | 8 | 0.0556 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 13 | 8 | 0.0384 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 30 | 8 | 0.0556 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 30 | 8 | 0.0556 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 31 | 8 | 0.0556 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 21 | 5 | 0.1855 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 24 | 4 | -0.0251 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 4 | -1.3085 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 33 | 3 | -1.1918 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 3 | -0.088 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 3 | -1.1918 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 2 | 0.629 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 2 | 0.629 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 46 | 1 | 4.1198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.1637 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `latency_state` | `caution` | 27 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 90 | 30 | -0.8635 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 90 | 30 | -0.8635 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 87 | 28 | -0.8365 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 21 | 20 | -1.3052 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 18 | 18 | -1.3122 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.2692 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -0.2692 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.2937 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.2937 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 2 | -1.2424 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 1 | -0.5849 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.2481 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 60 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 59 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 73 | 73 | -0.9277 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 73 | 73 | -0.9277 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 73 | 73 | -0.9277 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 71 | 71 | -1.148 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 52 | 52 | -1.0817 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 28 | 28 | -0.8611 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 27 | 27 | -0.4896 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 20 | 20 | -0.58 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 11 | 11 | -1.6546 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 10 | 10 | -0.71 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 10 | 10 | -0.9821 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 10 | 10 | 0.0198 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 8 | 8 | -0.8986 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -0.8726 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.2839 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.2839 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.2692 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.9615 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.6112 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 4 | 4 | -0.3675 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.2528 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.2482 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.9442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.4374 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.6503 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.13 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.3532 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 310 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 310 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 85 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 320, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2150 | 2147 | None | -0.9792 | 0.0736 | `hold_sample` |
| `qty_reason` | `qty_none` | 2147 | 2147 | None | -0.9792 | 0.0736 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2150 | 2147 | None | -0.9792 | 0.0736 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2150 | 2147 | None | -0.9792 | 0.0736 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2100 | 2100 | None | -1.0058 | 0.06 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1992 | 1989 | None | -1.1106 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1976 | 1973 | None | -1.0938 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1730 | 1730 | None | -1.1433 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1383 | 1383 | None | -1.4155 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1187 | 1187 | None | -0.9877 | 0.0868 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1016 | 1016 | None | -0.9334 | 0.1122 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 690 | 690 | None | -1.0439 | 0.0435 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 597 | 597 | None | -1.1592 | 0.0184 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 574 | 574 | None | -0.4348 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 359 | 359 | None | -0.5743 | 0.2869 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 318 | 318 | None | -1.0167 | 0.0346 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 222 | 222 | None | -0.7318 | 0.0946 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 205 | 205 | None | -0.6629 | 0.1025 | `hold_sample` |
| `arm` | `PYRAMID` | 158 | 158 | None | 0.6754 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 158 | 158 | None | 0.6754 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.2839 | -0.3786 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -0.3675 | -0.49 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 7 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | None | None | `hold_sample` |

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
