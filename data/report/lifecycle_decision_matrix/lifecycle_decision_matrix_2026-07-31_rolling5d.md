# Lifecycle Decision Matrix - 2026-07-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-31_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1741`
- source_rows_total: `3566`
- retained_rows: `1741`
- dropped_rows_by_source: `{}`
- joined_rows: `607`
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
- lifecycle_flow_bucket_count: `64`
- lifecycle_flow_complete_count: `9`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0084`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 912 | 8 | -0.5562 | 0.008 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 113 | 8 | -0.5562 | 0.041 | `pass` | `NO_CHANGE` | False |
| `holding` | 15 | 8 | -0.8897 | 0.1769 | `pass` | `EXIT` | False |
| `scale_in` | 571 | 565 | -0.7854 | 0.9927 | `pass` | `NO_CHANGE` | False |
| `exit` | 130 | 18 | -0.7093 | 0.2338 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 64, 'complete_flow_count': 9, 'incomplete_flow_count': 1058, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 482 | 476 | -1.0056 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 89 | 89 | 0.3926 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 1 | 1 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 1 | 1 | -1.1229 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:38511f6f01` | 1 | 1 | -0.6279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb99aaba9b` | 1 | 1 | -0.47 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b436f64c2` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:63a0b8330e` | 1 | 1 | -2.5775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 6 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:306834dafc` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 8 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:cf6cca51c3` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8a9ce220d7` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7f0fd369e2` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 203, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 92 | 7 | -0.6853 | -1.3771 | 0.1428 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 548 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 428 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 89 | 7 | -0.6853 | -1.3771 | 0.1428 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 89 | 7 | -0.6853 | -1.3771 | 0.1428 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 333 | 7 | -0.6853 | -1.3771 | 0.1428 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.3443 | -1.44 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 753 | 4 | -0.528 | -0.645 | 0.5 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 250 | 4 | -0.3443 | -1.44 | 0.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | -0.6619 | 0.0867 | 0.6667 | `hold_sample` |
| `score_band` | `score_63_65` | 88 | 3 | -0.4169 | -0.9733 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 282 | 3 | -0.6619 | 0.0867 | 0.6667 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 22 | 2 | -0.0004 | -1.46 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 8 | 2 | -0.6883 | -1.42 | 0.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 499 | 1 | 0.3474 | 0.09 | 1.0 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 407 | 1 | 0.3474 | 0.09 | 1.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 323 | 1 | 0.3474 | 0.09 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 178 | 1 | 0.3474 | 0.09 | 1.0 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 583 | 1 | 0.3474 | 0.09 | 1.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -1.0869 | -4.05 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 98, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 82 | 8 | -0.5562 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 10 | 8 | -0.5562 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 111 | 8 | -0.5562 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 11 | 8 | -0.5562 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 11 | 8 | -0.5562 | `keep_collecting` |
| `latency_state` | `simulated` | 11 | 8 | -0.5562 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 82 | 8 | -0.5562 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 11 | 8 | -0.5562 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 10 | 7 | -0.6853 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 9 | 6 | -0.3521 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 9 | 6 | -0.3521 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 79 | 6 | -0.3521 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 9 | 6 | -0.3521 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 9 | 6 | -0.3521 | `keep_collecting` |
| `would_limit_fill` | `false` | 109 | 5 | -0.5765 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 6 | 4 | -0.8075 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 2 | 2 | -1.1685 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2 | 2 | -1.1685 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 4 | 2 | -1.1685 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2 | 2 | -1.1685 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.1685 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 2 | 2 | -1.1685 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2 | 2 | -1.1685 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 1 | 1 | 0.3474 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 1 | 0.77 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 0.3474 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 2 | 1 | 0.77 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 26 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 26 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 72 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 13 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 1 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 31 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 70 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 20, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 11 | 8 | -0.8897 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 11 | 8 | -0.8897 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 9 | 7 | -1.0463 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 5 | 5 | -1.2427 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.2427 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | -0.3012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.5551 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 9 | 9 | -1.226 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 8 | 8 | -0.8897 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 6 | 6 | -0.8266 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 6 | 6 | -0.8266 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 6 | 6 | -0.8266 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 5 | 5 | -0.898 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 5 | 5 | -0.232 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | -0.1434 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.9091 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 4 | 4 | -1.205 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | -0.3012 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.9458 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.7457 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.2107 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -0.7356 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -2.5775 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 1 | 1 | -0.47 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.5775 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 112 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 112 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 90 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 90 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 22 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 22 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 90 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 22 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 114, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 570 | 565 | None | -0.8822 | 0.1575 | `hold_sample` |
| `qty_reason` | `qty_none` | 566 | 565 | None | -0.8822 | 0.1575 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 565 | 565 | None | -0.8822 | 0.1575 | `hold_sample` |
| `time_bucket` | `time_unknown` | 571 | 565 | None | -0.8822 | 0.1575 | `hold_sample` |
| `arm` | `AVG_DOWN` | 482 | 476 | None | -1.1145 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 478 | 472 | None | -1.0954 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 342 | 342 | None | -1.3943 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 327 | 321 | None | -0.7331 | 0.2772 | `hold_sample` |
| `ai_score_source` | `live` | 281 | 281 | None | -1.125 | 0.057 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 250 | 244 | None | -1.0784 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 193 | 193 | None | -0.6894 | 0.2487 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 185 | 185 | None | -0.5262 | 0.3784 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 179 | 179 | None | -0.4136 | 0.4972 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 146 | 146 | None | -1.5729 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 142 | 142 | None | -1.1359 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 128 | 128 | None | -0.4683 | 0.3125 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 120 | 120 | None | -0.4375 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 103 | 103 | None | 0.3002 | 0.8641 | `hold_sample` |
| `arm` | `PYRAMID` | 89 | 89 | None | 0.36 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 89 | 89 | None | 0.36 | 1.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 16, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |

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
