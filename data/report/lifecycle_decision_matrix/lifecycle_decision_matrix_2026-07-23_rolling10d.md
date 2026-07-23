# Lifecycle Decision Matrix - 2026-07-23

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-23_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4346`
- source_rows_total: `11270`
- retained_rows: `4346`
- dropped_rows_by_source: `{}`
- joined_rows: `2093`
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
- lifecycle_flow_bucket_count: `105`
- lifecycle_flow_complete_count: `60`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0207`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1529 | 14 | 0.0922 | 0.0152 | `pass` | `NO_CHANGE` | False |
| `submit` | 395 | 21 | 0.0705 | 0.1012 | `pass` | `NO_CHANGE` | False |
| `holding` | 94 | 21 | -0.581 | 0.2405 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 1945 | 1943 | -0.7956 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 383 | 94 | -0.7878 | 0.6692 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 105, 'complete_flow_count': 60, 'incomplete_flow_count': 2841, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1793 | 1791 | -0.9205 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 151 | 151 | 0.6863 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 16 | 16 | -0.8625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 2 | 2 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 2 | 2 | -0.835 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:65653fdfbd` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:36ac2952b0` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b9452e4761` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:1f33988758` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e7d176584e` | 1 | 1 | -0.67 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 186, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overbought_bucket` | `overbought_normal` | 435 | 13 | 0.2478 | -1.1703 | 0.3077 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1270 | 13 | 0.1317 | -0.9885 | 0.3846 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 640 | 12 | 0.3036 | -1.1758 | 0.3333 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 387 | 12 | 0.3036 | -1.1758 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_high` | 399 | 9 | 0.0839 | -0.5433 | 0.4444 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 323 | 8 | 0.2614 | -0.5113 | 0.5 | `hold_sample` |
| `score_band` | `score_lt60` | 1267 | 7 | 0.4805 | -1.4414 | 0.2857 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 222 | 7 | 0.5395 | -2.412 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 535 | 6 | -0.2758 | 0.34 | 0.6667 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | 0.5119 | -1.482 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.7389 | 1.18 | 1.0 | `hold_sample` |
| `score_band` | `score_60_62` | 141 | 4 | -0.0395 | -0.64 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 80 | 3 | 0.9626 | -3.0733 | 0.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 833 | 3 | -0.2224 | -0.5633 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | 0.9489 | -3.78 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 85 | 3 | 0.2695 | -0.5467 | 0.3333 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 101 | 3 | -0.0445 | -2.7246 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 731 | 2 | -1.1766 | 0.078 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 26 | 2 | -0.266 | 1.21 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 14 | 2 | 0.4145 | -2.535 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 115, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 320 | 21 | 0.0705 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 358 | 21 | 0.0705 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 87 | 21 | 0.0705 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 87 | 21 | 0.0705 | `keep_collecting` |
| `latency_state` | `simulated` | 87 | 21 | 0.0705 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 320 | 21 | 0.0705 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 87 | 21 | 0.0705 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 85 | 20 | -0.0539 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 76 | 16 | -0.2418 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 61 | 15 | 0.0586 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 60 | 15 | 0.0586 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 284 | 15 | 0.0586 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 60 | 15 | 0.0586 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 61 | 15 | 0.0586 | `keep_collecting` |
| `would_limit_fill` | `false` | 343 | 9 | 0.2069 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 33 | 8 | -0.087 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 26 | 6 | 0.1001 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 27 | 6 | 0.1001 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 26 | 6 | 0.1001 | `keep_collecting` |
| `would_limit_fill` | `true` | 25 | 6 | -0.1638 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 26 | 6 | 0.1001 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 27 | 6 | 0.1001 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 11 | 5 | 1.0696 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 21 | 4 | 0.1278 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 21 | 3 | 0.142 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 36 | 2 | -1.9726 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 2 | -0.747 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 2 | 0.1312 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 2 | -1.9726 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 1 | 2.5584 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 52 | 1 | 4.1198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 1 | 2.5584 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 0.1637 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `latency_state` | `caution` | 32 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 87 | 21 | -0.581 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 87 | 21 | -0.581 | `hold_sample` |
| `holding_action` | `WAIT` | 84 | 19 | -0.5113 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 13 | -1.0441 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.0081 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.3247 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | -0.3247 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 2 | -1.2424 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 1.0046 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 1.0046 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 1 | -0.5849 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.2481 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 66 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 65 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 68 | 68 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 68 | 68 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 68 | 68 | -0.9068 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 63 | 63 | -1.0392 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 51 | 51 | -1.0341 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 23 | 23 | -0.4639 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 19 | 19 | -0.5477 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 16 | 16 | -0.5656 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 9 | 9 | -0.4669 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | 0.1717 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.2839 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.2839 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 6 | 6 | -0.8157 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -1.5533 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.4918 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -0.3273 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.3247 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.4773 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3 | 3 | -0.4325 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.713 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.4374 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.6692 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.3152 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 1 | 1 | -0.9525 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.13 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.3532 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 289 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 289 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 83 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 83 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 206 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 308, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1945 | 1943 | None | -0.9195 | 0.0777 | `hold_sample` |
| `qty_reason` | `qty_none` | 1943 | 1943 | None | -0.9195 | 0.0777 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1945 | 1943 | None | -0.9195 | 0.0777 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1928 | 1926 | None | -0.9237 | 0.0784 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1900 | 1900 | None | -0.9454 | 0.0637 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1794 | 1792 | None | -1.0536 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1785 | 1783 | None | -1.0428 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1632 | 1632 | None | -1.109 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1207 | 1207 | None | -1.3651 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1064 | 1064 | None | -0.9055 | 0.094 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 919 | 919 | None | -0.902 | 0.1229 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 637 | 637 | None | -1.0218 | 0.0471 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 554 | 554 | None | -0.4308 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 520 | 520 | None | -1.0884 | 0.0135 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 296 | 296 | None | -0.9059 | 0.0338 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 239 | 239 | None | -0.1943 | 0.4142 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 198 | 198 | None | -0.6133 | 0.101 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 188 | 188 | None | -0.6647 | 0.0851 | `hold_sample` |
| `arm` | `PYRAMID` | 151 | 151 | None | 0.6721 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 151 | 151 | None | 0.6721 | 1.0 | `hold_sample` |

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
