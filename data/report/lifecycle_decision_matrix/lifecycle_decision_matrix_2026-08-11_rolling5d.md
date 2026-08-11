# Lifecycle Decision Matrix - 2026-08-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-11_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3166`
- source_rows_total: `3325`
- retained_rows: `3166`
- dropped_rows_by_source: `{}`
- joined_rows: `1332`
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
- lifecycle_flow_bucket_count: `53`
- lifecycle_flow_complete_count: `17`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0094`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1747 | 17 | -0.1615 | 0.0166 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 68 | 17 | -0.1615 | 0.4 | `pass` | `NO_CHANGE` | False |
| `holding` | 18 | 17 | -0.5676 | 0.7824 | `pass` | `EXIT` | False |
| `scale_in` | 1275 | 1260 | -1.0029 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 58 | 21 | -0.5731 | 0.7004 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 53, 'complete_flow_count': 17, 'incomplete_flow_count': 1785, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1170 | 1156 | -1.1339 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 105 | 104 | 0.4529 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 1 | 1 | -0.904 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f3f2837f26` | 1 | 1 | -1.6262 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7e17ca9764` | 1 | 1 | -2.1951 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 1 | 1 | -0.74 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ce05b30c9f` | 1 | 1 | -0.9949 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | -1.36 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:db2aa0a4af` | 1 | 1 | -1.632 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:46ace3ddee` | 1 | 1 | 0.8311 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 240, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 159 | 15 | -0.1781 | -1.1293 | 0.4 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 569 | 15 | -0.1781 | -1.1293 | 0.4 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 346 | 15 | -0.1781 | -1.1293 | 0.4 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 149 | 15 | -0.1781 | -1.1293 | 0.4 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 149 | 15 | -0.1781 | -1.1293 | 0.4 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 460 | 15 | -0.1781 | -1.1293 | 0.4 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 166 | 12 | -0.2156 | -0.6358 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.7783 | 0.5725 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 466 | 7 | 0.5085 | -1.2871 | 0.2857 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 6 | 6 | 0.6521 | -1.52 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 56 | 6 | -0.3518 | -0.7667 | 0.5 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 471 | 6 | -0.3518 | -0.7667 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 17 | 5 | 0.6121 | -0.7 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -0.1438 | -3.7233 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 23 | 3 | -0.0277 | -3.1033 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 284 | 3 | -1.3139 | -0.9367 | 0.6667 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1368 | 2 | -0.0371 | 0.615 | 1.0 | `hold_sample` |
| `stale_bucket` | `fresh` | 1151 | 2 | -0.0371 | 0.615 | 1.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1071 | 2 | -0.0371 | 0.615 | 1.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 346 | 2 | -0.0371 | 0.615 | 1.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 78, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 68 | 17 | -0.1615 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 66 | 17 | -0.1615 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 18 | 17 | -0.1615 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 18 | 17 | -0.1615 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 18 | 17 | -0.1615 | `keep_collecting` |
| `latency_state` | `simulated` | 18 | 17 | -0.1615 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 68 | 17 | -0.1615 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 18 | 17 | -0.1615 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 17 | 16 | -0.1558 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 13 | 12 | 0.1415 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 12 | 12 | 0.1415 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 61 | 12 | 0.1415 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 12 | 12 | 0.1415 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 13 | 12 | 0.1415 | `keep_collecting` |
| `would_limit_fill` | `false` | 57 | 7 | -0.1121 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 7 | -0.1121 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 5 | 5 | -0.8886 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 6 | 5 | -0.8886 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 5 | 5 | -0.8886 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 5 | 0.4966 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 5 | 5 | 0.4966 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 5 | 5 | -0.8886 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 6 | 5 | -0.8886 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 5 | 4 | -1.2287 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -1.2287 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | -0.2518 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1 | 1 | 0.4716 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.4716 | `source_quality_workorder` |
| `latency_state` | `danger` | 49 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 49 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 50 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 16, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 17 | 17 | -0.5676 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 17 | 17 | -0.5676 | `hold_sample` |
| `holding_action` | `WAIT` | 16 | 16 | -0.6172 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 9 | 9 | -0.956 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -0.956 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | -0.3057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.412 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.3948 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.3948 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | 0.2255 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2255 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 18 | 18 | -0.5425 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 11 | 11 | -0.9731 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -0.1306 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 6 | 6 | -0.9869 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.0083 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 6 | 6 | -0.6322 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | -0.3057 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 6 | 6 | -0.4434 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.1905 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.9812 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.7104 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2 | 2 | -1.05 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 2 | -0.1437 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.3948 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1437 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2 | 2 | -1.05 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2 | 2 | -1.05 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.05 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.9495 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.8743 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | 0.2081 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.1951 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -0.0415 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 0.8311 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 37 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 29 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 29 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 8 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 8 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 29 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 8 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 142, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1275 | 1260 | None | -1.0855 | 0.0825 | `hold_sample` |
| `qty_reason` | `qty_none` | 1260 | 1260 | None | -1.0855 | 0.0825 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1275 | 1260 | None | -1.0855 | 0.0825 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1259 | 1258 | None | -1.0878 | 0.0811 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1170 | 1156 | None | -1.2217 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1168 | 1154 | None | -1.2183 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 914 | 914 | None | -1.4291 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 683 | 683 | None | -1.099 | 0.0322 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 692 | 677 | None | -0.9741 | 0.1536 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 664 | 664 | None | -1.0427 | 0.0738 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 600 | 585 | None | -1.2099 | 0.0034 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 533 | 533 | None | -1.2888 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 296 | 296 | None | -1.1199 | 0.2162 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 257 | 257 | None | -1.4047 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 253 | 253 | None | -1.0593 | 0.166 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 212 | 212 | None | -0.4969 | 0.0 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 185 | 185 | None | -1.2204 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 167 | 167 | None | -1.078 | 0.042 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 149 | 149 | None | -1.1159 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 137 | 137 | None | 0.1651 | 0.708 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 15, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 1 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | None | None | `hold_sample` |

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
