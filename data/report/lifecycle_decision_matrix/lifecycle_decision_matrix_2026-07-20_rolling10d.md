# Lifecycle Decision Matrix - 2026-07-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-20_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3439`
- source_rows_total: `8345`
- retained_rows: `3439`
- dropped_rows_by_source: `{}`
- joined_rows: `1887`
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
- lifecycle_flow_bucket_count: `99`
- lifecycle_flow_complete_count: `52`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0211`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1005 | 15 | -0.3755 | 0.0218 | `pass` | `NO_CHANGE` | False |
| `submit` | 239 | 23 | -0.2879 | 0.147 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 78 | 23 | -0.9257 | 0.3299 | `pass` | `EXIT` | False |
| `scale_in` | 1742 | 1739 | -0.907 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 375 | 87 | -0.909 | 0.708 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 99, 'complete_flow_count': 52, 'incomplete_flow_count': 2415, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1602 | 1599 | -1.0356 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 126 | 126 | 0.7466 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 13 | 13 | -1.0162 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 7 | 7 | -0.8914 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 1 | 1 | -1.8153 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:65653fdfbd` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:36ac2952b0` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b9452e4761` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:1f33988758` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 1 | 1 | -0.89 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e7d176584e` | 1 | 1 | -0.67 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce1fde0c73` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 176, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 788 | 15 | -0.3755 | -1.3873 | 0.4667 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 502 | 10 | 0.0923 | -1.663 | 0.4 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 331 | 10 | 0.0923 | -1.663 | 0.4 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 279 | 10 | -0.0357 | -1.638 | 0.4 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 365 | 9 | 0.1759 | -1.29 | 0.4444 | `hold_sample` |
| `stale_bucket` | `stale_high` | 318 | 9 | -0.4287 | -0.9744 | 0.5556 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -1.0466 | 1.04 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | 0.331 | -3.5383 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 758 | 6 | 0.0924 | -1.2367 | 0.5 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 130 | 6 | 0.2091 | -2.82 | 0.1666 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 319 | 6 | -0.3857 | -0.2633 | 0.6667 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 608 | 5 | -1.311 | -0.836 | 0.6 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 559 | 5 | -1.311 | -0.836 | 0.6 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 145 | 5 | -0.1864 | -1.586 | 0.4 | `hold_sample` |
| `score_band` | `score_70p` | 86 | 4 | -1.3137 | -1.365 | 0.5 | `hold_sample` |
| `stale_bucket` | `stale_watch` | 89 | 4 | -1.056 | -1.07 | 0.5 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 395 | 3 | -1.8904 | -0.6467 | 0.6667 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 481 | 3 | -1.8542 | 0.88 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 268 | 3 | -1.524 | -0.77 | 0.6667 | `source_quality_workorder` |
| `chosen_action` | `BUY_DEFENSIVE` | 28 | 2 | -0.4418 | -1.12 | 0.5 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 201 | 23 | -0.2879 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 224 | 23 | -0.2879 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 73 | 23 | -0.2879 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 73 | 23 | -0.2879 | `keep_collecting` |
| `latency_state` | `simulated` | 73 | 23 | -0.2879 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 201 | 23 | -0.2879 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 73 | 23 | -0.2879 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 70 | 21 | -0.3752 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 63 | 17 | -0.3722 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 44 | 16 | -0.4314 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 43 | 16 | -0.4314 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 169 | 16 | -0.4314 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 43 | 16 | -0.4314 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 44 | 16 | -0.4314 | `keep_collecting` |
| `would_limit_fill` | `false` | 192 | 10 | -0.085 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 23 | 8 | -0.2634 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 29 | 7 | 0.0401 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 29 | 7 | 0.0401 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 29 | 7 | 0.0401 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 29 | 7 | 0.0401 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 30 | 7 | 0.0401 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 10 | 6 | -0.0489 | `keep_collecting` |
| `would_limit_fill` | `true` | 17 | 6 | -1.0087 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 21 | 3 | -0.088 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 23 | 3 | -1.1918 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 3 | -1.8904 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 3 | -0.127 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 3 | -0.088 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 3 | -1.1918 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 2 | 0.629 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 2 | 0.629 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 25 | 1 | 4.1198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `latency_state` | `caution` | 18 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 18 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 73 | 23 | -0.9257 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 73 | 23 | -0.9257 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 71 | 22 | -0.929 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 14 | 13 | -1.6531 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 12 | 12 | -1.7196 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.2692 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -0.2692 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.2937 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.2937 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2 | 1 | -0.8553 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 5 | 1 | -0.5849 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.8553 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 50 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 49 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 60 | 60 | -0.957 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 60 | 60 | -0.957 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 60 | 60 | -0.957 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 56 | 56 | -1.2349 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 43 | 43 | -1.1158 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 22 | 22 | -0.9101 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 21 | 21 | -0.5164 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 16 | 16 | -0.5981 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -1.6572 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 10 | 10 | 0.0198 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 8 | 8 | -0.8986 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 8 | 8 | -0.9553 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.8651 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 5 | 5 | -0.3285 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.2692 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.3285 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.3285 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.2528 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -1.6066 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.2482 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.9442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.4374 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.8247 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.13 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.8982 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7511 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.3532 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.1279 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 288 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 288 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 69 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 69 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 219 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 298, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1742 | 1739 | None | -1.0588 | 0.0725 | `hold_sample` |
| `qty_reason` | `qty_none` | 1739 | 1739 | None | -1.0588 | 0.0725 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1742 | 1739 | None | -1.0588 | 0.0725 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1742 | 1739 | None | -1.0588 | 0.0725 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1695 | 1695 | None | -1.0943 | 0.0555 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1616 | 1613 | None | -1.1993 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1603 | 1600 | None | -1.1835 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1383 | 1383 | None | -1.2385 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1199 | 1199 | None | -1.4717 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 971 | 971 | None | -1.0745 | 0.0834 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 816 | 816 | None | -1.0165 | 0.1078 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 561 | 561 | None | -1.1174 | 0.0428 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 504 | 504 | None | -1.2272 | 0.0218 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 389 | 389 | None | -0.4328 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 305 | 305 | None | -0.6637 | 0.2492 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 257 | 257 | None | -1.098 | 0.0311 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 178 | 178 | None | -0.7557 | 0.1123 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 152 | 152 | None | -0.7159 | 0.1184 | `hold_sample` |
| `arm` | `PYRAMID` | 126 | 126 | None | 0.7403 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 126 | 126 | None | 0.7403 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -0.3285 | -0.438 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -0.4325 | -0.5767 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.9525 | -1.27 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 5 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | None | None | `hold_sample` |

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
