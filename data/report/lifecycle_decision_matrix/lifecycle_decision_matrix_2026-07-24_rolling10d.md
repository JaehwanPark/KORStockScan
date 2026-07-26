# Lifecycle Decision Matrix - 2026-07-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-24_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3981`
- source_rows_total: `10208`
- retained_rows: `3981`
- dropped_rows_by_source: `{}`
- joined_rows: `1756`
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
- lifecycle_flow_bucket_count: `101`
- lifecycle_flow_complete_count: `44`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0173`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1575 | 14 | 0.0922 | 0.0152 | `pass` | `NO_CHANGE` | False |
| `submit` | 373 | 20 | 0.1375 | 0.1061 | `pass` | `NO_CHANGE` | False |
| `holding` | 72 | 20 | -0.5465 | 0.2523 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 1628 | 1626 | -0.713 | 0.9987 | `pass` | `NO_CHANGE` | False |
| `exit` | 333 | 76 | -0.7129 | 0.6521 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 44, 'incomplete_flow_count': 2495, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1479 | 1477 | -0.8549 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 149 | 149 | 0.6939 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 13 | 13 | -0.8169 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 2 | 2 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 1 | 1 | -1.07 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:65653fdfbd` | 1 | 1 | -0.97 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b9452e4761` | 1 | 1 | -0.65 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 1 | 1 | -0.74 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:1f33988758` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e7d176584e` | 1 | 1 | -0.67 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bbdffe02a7` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:5a753e3e56` | 1 | 1 | -1.5656 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 181, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overbought_bucket` | `overbought_normal` | 442 | 13 | 0.2478 | -1.1703 | 0.3077 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1332 | 13 | 0.1317 | -0.9885 | 0.3846 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 643 | 12 | 0.3036 | -1.1758 | 0.3333 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 413 | 12 | 0.3036 | -1.1758 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_high` | 382 | 9 | 0.0839 | -0.5433 | 0.4444 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 320 | 8 | 0.2614 | -0.5113 | 0.5 | `hold_sample` |
| `score_band` | `score_lt60` | 1302 | 7 | 0.4805 | -1.4414 | 0.2857 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 241 | 7 | 0.5395 | -2.412 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 523 | 6 | -0.2758 | 0.34 | 0.6667 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | 0.5119 | -1.482 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | -0.7389 | 1.18 | 1.0 | `hold_sample` |
| `score_band` | `score_60_62` | 117 | 4 | -0.0395 | -0.64 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 117 | 3 | 0.9626 | -3.0733 | 0.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 884 | 3 | -0.2224 | -0.5633 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | 0.9489 | -3.78 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 80 | 3 | 0.2695 | -0.5467 | 0.3333 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 90 | 3 | -0.0445 | -2.7246 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 753 | 2 | -1.1766 | 0.078 | 0.5 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 25 | 2 | -0.266 | 1.21 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 12 | 2 | 0.4145 | -2.535 | 0.0 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 302 | 20 | 0.1375 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 339 | 20 | 0.1375 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 65 | 20 | 0.1375 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 65 | 20 | 0.1375 | `keep_collecting` |
| `latency_state` | `simulated` | 65 | 20 | 0.1375 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 302 | 20 | 0.1375 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 65 | 20 | 0.1375 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 63 | 19 | 0.0101 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 55 | 15 | -0.1732 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 47 | 14 | 0.1536 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 47 | 14 | 0.1536 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 276 | 14 | 0.1536 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 47 | 14 | 0.1536 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 47 | 14 | 0.1536 | `keep_collecting` |
| `would_limit_fill` | `false` | 335 | 8 | 0.3915 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 25 | 7 | 0.082 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 18 | 6 | 0.1001 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 18 | 6 | 0.1001 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 18 | 6 | 0.1001 | `keep_collecting` |
| `would_limit_fill` | `true` | 20 | 6 | -0.1638 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 18 | 6 | 0.1001 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 18 | 6 | 0.1001 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 10 | 5 | 1.0696 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 4 | 0.1278 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 12 | 3 | 0.142 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 34 | 2 | -1.9726 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 2 | -0.747 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 2 | 0.1312 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 2 | -1.9726 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 1 | 2.5584 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 49 | 1 | 4.1198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 1 | 2.5584 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1637 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `latency_state` | `caution` | 30 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 65 | 20 | -0.5465 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 65 | 20 | -0.5465 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 62 | 18 | -0.4692 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 12 | 12 | -1.0253 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -0.9819 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.3247 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | -0.3247 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 3 | 2 | -1.2424 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 1.0046 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 1.0046 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 1 | -0.5849 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.2481 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 45 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 44 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 50 | 50 | -0.8514 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 50 | 50 | -0.8514 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 50 | 50 | -0.8514 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 48 | 48 | -0.9954 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 37 | 37 | -0.973 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 20 | 20 | -0.4246 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 19 | 19 | -0.5477 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 12 | 12 | -0.5583 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 9 | 9 | -0.4669 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | 0.1717 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 6 | 6 | -0.8157 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -1.5533 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 5 | 5 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.4918 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -0.3273 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | -0.3247 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.4773 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.713 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.4374 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.6692 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.3152 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.13 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | -0.3532 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.5849 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 257 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 257 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 61 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 61 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 196 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 196 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 275, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1628 | 1626 | None | -0.8144 | 0.0917 | `hold_sample` |
| `qty_reason` | `qty_none` | 1626 | 1626 | None | -0.8144 | 0.0917 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1628 | 1626 | None | -0.8144 | 0.0917 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1608 | 1606 | None | -0.8176 | 0.0928 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1586 | 1586 | None | -0.8435 | 0.075 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1479 | 1477 | None | -0.9652 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1471 | 1469 | None | -0.9529 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1316 | 1316 | None | -1.0214 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 930 | 930 | None | -1.2916 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 887 | 887 | None | -0.7926 | 0.1116 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 861 | 861 | None | -0.8437 | 0.1312 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 549 | 549 | None | -0.9234 | 0.0528 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 518 | 518 | None | -0.4297 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 375 | 375 | None | -0.8959 | 0.016 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 235 | 235 | None | -0.1971 | 0.4128 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 217 | 217 | None | -0.7975 | 0.0415 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 164 | 164 | None | -0.5299 | 0.122 | `hold_sample` |
| `arm` | `PYRAMID` | 149 | 149 | None | 0.6796 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 149 | 149 | None | 0.6796 | 1.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 144 | 144 | None | -0.5548 | 0.1111 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 0 | None | None | None | `hold_sample` |
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
