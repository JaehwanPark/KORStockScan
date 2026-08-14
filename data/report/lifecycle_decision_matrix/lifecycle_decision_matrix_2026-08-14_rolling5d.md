# Lifecycle Decision Matrix - 2026-08-14

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-14_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `9700`
- source_rows_total: `11123`
- retained_rows: `9700`
- dropped_rows_by_source: `{}`
- joined_rows: `4249`
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
- lifecycle_flow_bucket_count: `88`
- lifecycle_flow_complete_count: `32`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0045`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2952 | 30 | -0.1743 | 0.0121 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 273 | 42 | -0.453 | 0.2906 | `pass` | `NO_CHANGE` | False |
| `holding` | 70 | 42 | -0.7338 | 0.6842 | `pass` | `EXIT` | False |
| `scale_in` | 4132 | 4085 | -0.8111 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2273 | 50 | -0.489 | 0.3116 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 88, 'complete_flow_count': 32, 'incomplete_flow_count': 7136, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3879 | 3833 | -0.8858 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 253 | 252 | 0.3251 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 2 | 2 | -1.86 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:f2f4676367` | 1 | 1 | 0.1639 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 1 | 1 | -0.34 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:927a4c8e9e` | 1 | 1 | -0.2151 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f15e79e2f2` | 1 | 1 | -1.3447 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 293, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 215 | 19 | -0.2561 | -1.2842 | 0.3158 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1362 | 19 | -0.2561 | -1.2842 | 0.3158 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1125 | 19 | -0.2561 | -1.2842 | 0.3158 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 196 | 19 | -0.2561 | -1.2842 | 0.3158 | `hold_no_edge` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 196 | 19 | -0.2561 | -1.2842 | 0.3158 | `hold_no_edge` |
| `stale_bucket` | `stale_not_available` | 912 | 19 | -0.2561 | -1.2842 | 0.3158 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 234 | 15 | -0.2021 | -0.8047 | 0.4 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 749 | 14 | -0.2522 | -0.91 | 0.3571 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | 0.2072 | -1.4954 | 0.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1821 | 11 | -0.0332 | -1.0173 | 0.4545 | `hold_sample` |
| `stale_bucket` | `fresh` | 1795 | 11 | -0.0332 | -1.0173 | 0.4545 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1520 | 11 | -0.0332 | -1.0173 | 0.4545 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2205 | 11 | -0.0332 | -1.0173 | 0.4545 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | -0.6486 | 0.4855 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 123 | 10 | -0.2568 | -1.282 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 73 | 9 | -0.2838 | -1.0044 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 526 | 8 | 0.2262 | -1.5037 | 0.25 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1446 | 8 | 0.1672 | -0.8075 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 497 | 6 | -0.1235 | -0.9433 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -0.1316 | -3.5816 | 0.0 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 258 | 42 | -0.453 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 269 | 42 | -0.453 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 66 | 42 | -0.453 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 66 | 42 | -0.453 | `keep_collecting` |
| `latency_state` | `simulated` | 66 | 42 | -0.453 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 258 | 42 | -0.453 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 66 | 42 | -0.453 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 50 | 33 | -0.3152 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 44 | 25 | 0.0189 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 28 | 25 | -0.3507 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 43 | 25 | 0.0189 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 229 | 25 | 0.0189 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 43 | 25 | 0.0189 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 44 | 25 | 0.0189 | `keep_collecting` |
| `would_limit_fill` | `false` | 240 | 18 | -0.1607 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 26 | 17 | -1.1469 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 41 | 17 | -0.6033 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 21 | 17 | -1.1469 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 22 | 17 | -1.1469 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 23 | 17 | -1.1469 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 21 | 16 | -1.0742 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 37 | 16 | -1.248 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 12 | 10 | -0.2344 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 8 | -0.0686 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -1.1687 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 8 | -1.3273 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 12 | 7 | -1.1511 | `keep_collecting` |
| `would_limit_fill` | `true` | 10 | 7 | 0.481 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 6 | 0.4092 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 4 | 2 | -0.2814 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 3 | 1 | 0.4716 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 2 | 1 | -2.31 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 1 | 0.9116 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.4716 | `source_quality_workorder` |
| `latency_state` | `caution` | 13 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 64 | 42 | -0.7338 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 64 | 42 | -0.7338 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 48 | 32 | -0.749 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 24 | 22 | -1.1221 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 20 | 20 | -1.0141 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 12 | 12 | -0.494 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 16 | 10 | -0.6852 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.4393 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.5487 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.4603 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.4087 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.4603 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3948 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.2024 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.4227 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 22 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 40 | 40 | -0.4214 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 24 | 24 | -1.0648 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 19 | 19 | 0.1571 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 18 | 18 | -0.189 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -0.5964 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 12 | 12 | -0.9954 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 12 | 12 | -0.494 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 10 | 10 | -0.151 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 8 | 8 | -0.3464 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.801 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.6743 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 6 | 6 | -0.7675 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.7675 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -1.896 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 6 | 6 | -0.7851 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.1196 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.2196 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.4087 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 4 | 4 | -0.7475 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.2212 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.0565 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 2 | 2 | -1.86 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.055 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.44 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.9749 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.1401 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.6774 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.2568 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 2223 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 2223 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2223 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 2223 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 231, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 4132 | 4085 | None | -0.884 | 0.0575 | `hold_sample` |
| `qty_reason` | `qty_none` | 4085 | 4085 | None | -0.884 | 0.0575 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4132 | 4085 | None | -0.884 | 0.0575 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4079 | 4078 | None | -0.886 | 0.0562 | `hold_sample` |
| `arm` | `AVG_DOWN` | 3879 | 3833 | None | -0.9619 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3873 | 3827 | None | -0.9581 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2653 | 2653 | None | -1.183 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2203 | 2156 | None | -0.8177 | 0.109 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2119 | 2119 | None | -0.8927 | 0.0614 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2117 | 2117 | None | -0.9806 | 0.042 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1981 | 1934 | None | -0.9556 | 0.0021 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1629 | 1629 | None | -0.9891 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1092 | 1092 | None | -0.4985 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1075 | 1075 | None | -0.7962 | 0.0949 | `hold_sample` |
| `ai_score_source` | `live` | 1060 | 1060 | None | -0.8583 | 0.0793 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 607 | 607 | None | -1.0909 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 570 | 570 | None | -0.7664 | 0.0509 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 509 | 509 | None | -0.3169 | 0.4302 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 490 | 490 | None | -0.9568 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 438 | 438 | None | -1.006 | 0.0068 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 12 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 6 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 12 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `stage` | `exit` | 6 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 12 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 12 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.7675 | -1.0233 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2212 | -0.295 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -1.3625 | -1.8167 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -1.86 | -2.48 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 6 | 0 | None | None | None | `hold_sample` |

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
