# Lifecycle Decision Matrix - 2026-08-14

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-14_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `12749`
- source_rows_total: `14476`
- retained_rows: `12749`
- dropped_rows_by_source: `{}`
- joined_rows: `4796`
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
- lifecycle_flow_bucket_count: `107`
- lifecycle_flow_complete_count: `40`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0047`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5257 | 38 | -0.2278 | 0.0099 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 347 | 50 | -0.449 | 0.2777 | `pass` | `NO_CHANGE` | False |
| `holding` | 79 | 50 | -0.7207 | 0.6201 | `pass` | `EXIT` | False |
| `scale_in` | 4639 | 4591 | -0.8284 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2427 | 67 | -0.5409 | 0.2501 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 107, 'complete_flow_count': 40, 'incomplete_flow_count': 8469, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4344 | 4297 | -0.909 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 295 | 294 | 0.35 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 2 | 2 | -0.625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 2 | 2 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 336, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 355 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 2147 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1620 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 311 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 311 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 1505 | 24 | -0.3261 | -1.4079 | 0.2917 | `hold_sample` |
| `score_band` | `score_63_65` | 451 | 21 | -0.3039 | -0.9576 | 0.381 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1403 | 17 | -0.3854 | -1.2276 | 0.2941 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 15 | 15 | 0.21 | -1.4873 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.4883 | 0.538 | 1.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 3547 | 14 | -0.0593 | -0.615 | 0.5714 | `hold_sample` |
| `stale_bucket` | `fresh` | 3289 | 14 | -0.0593 | -0.615 | 0.5714 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2823 | 14 | -0.0593 | -0.615 | 0.5714 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3779 | 14 | -0.0593 | -0.615 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 106 | 12 | -0.4646 | -1.4308 | 0.25 | `hold_sample` |
| `score_band` | `score_70p` | 176 | 12 | -0.2202 | -0.9658 | 0.5 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 1044 | 10 | 0.1205 | -1.209 | 0.3 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 2826 | 9 | 0.1052 | -0.5678 | 0.5556 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -0.5601 | -3.52 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1178 | 8 | -0.4114 | -1.3913 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 103, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 332 | 50 | -0.449 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 341 | 50 | -0.449 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 74 | 50 | -0.449 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 74 | 50 | -0.449 | `keep_collecting` |
| `latency_state` | `simulated` | 74 | 50 | -0.449 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 332 | 50 | -0.449 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 74 | 50 | -0.449 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 57 | 40 | -0.3394 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 35 | 32 | -0.3688 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 50 | 31 | 0.0239 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 49 | 31 | 0.0239 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 299 | 31 | 0.0239 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 49 | 31 | 0.0239 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 50 | 31 | 0.0239 | `keep_collecting` |
| `would_limit_fill` | `false` | 310 | 22 | -0.1321 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 28 | 19 | -1.2204 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 23 | 19 | -1.2204 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 24 | 19 | -1.2204 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 25 | 19 | -1.2204 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 23 | 18 | -1.1599 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 42 | 18 | -0.5915 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 38 | 17 | -1.215 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 16 | 14 | -0.1684 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -1.1151 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 12 | 9 | 0.4051 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 8 | -0.0686 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 8 | -1.3273 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 12 | 7 | -1.1511 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 7 | 0.4465 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 5 | 3 | -0.2715 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 4 | 2 | -1.2667 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 2 | 0.2605 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.2667 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 2 | 1 | -2.31 | `keep_collecting` |
| `latency_state` | `caution` | 13 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 27, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 72 | 50 | -0.7207 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 72 | 50 | -0.7207 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 55 | 39 | -0.7541 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 28 | 26 | -1.1975 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 24 | 24 | -1.1138 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 15 | 15 | -0.3434 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 17 | 11 | -0.6024 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.2605 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.4381 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.4183 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 9 | 4 | -0.4603 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.4603 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.4153 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.2024 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.4227 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 48 | 48 | -0.4599 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 32 | 32 | -1.1211 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | 0.1834 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -0.2544 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 16 | 16 | -0.5981 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 15 | 15 | -0.9707 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 15 | 15 | -0.3434 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.421 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 12 | 12 | -0.7825 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 12 | 12 | -0.7825 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 12 | 12 | -0.7825 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 11 | 11 | -0.1742 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -0.8024 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.6116 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -2.0758 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.6825 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.6825 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 7 | 7 | -0.6408 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 7 | 7 | -0.0781 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 6 | 6 | -0.9967 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 6 | 6 | -0.5683 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.1672 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.4183 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.3668 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.9609 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | 0.2455 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.6774 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 2360 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 2360 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 119 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 119 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 251, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4639 | 4591 | None | -0.9058 | 0.0603 | `hold_sample` |
| `qty_reason` | `qty_none` | 4591 | 4591 | None | -0.9058 | 0.0603 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4639 | 4591 | None | -0.9058 | 0.0603 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4571 | 4570 | None | -0.9128 | 0.0562 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4344 | 4297 | None | -0.99 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4336 | 4289 | None | -0.9857 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2942 | 2942 | None | -1.2295 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2479 | 2431 | None | -0.8343 | 0.1139 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2338 | 2338 | None | -0.95 | 0.05 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2282 | 2282 | None | -0.9026 | 0.0587 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2213 | 2165 | None | -0.9839 | 0.0018 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1767 | 1767 | None | -1.037 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1260 | 1260 | None | -0.5017 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1233 | 1233 | None | -0.881 | 0.0949 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1191 | 1191 | None | -0.8733 | 0.0882 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 692 | 692 | None | -1.1488 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 673 | 673 | None | -0.8847 | 0.058 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 638 | 638 | None | -0.336 | 0.3965 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 531 | 531 | None | -0.9525 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 493 | 493 | None | -1.0138 | 0.0061 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.6825 | -0.91 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.2115 | -0.282 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.2975 | -1.73 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -1.3625 | -1.8167 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 7 | 0 | None | None | None | `hold_sample` |

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
