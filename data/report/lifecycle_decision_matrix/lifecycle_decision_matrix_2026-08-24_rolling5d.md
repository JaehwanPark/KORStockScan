# Lifecycle Decision Matrix - 2026-08-24

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-24_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `5292`
- source_rows_total: `6700`
- retained_rows: `5292`
- dropped_rows_by_source: `{}`
- joined_rows: `2382`
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
- lifecycle_flow_bucket_count: `65`
- lifecycle_flow_complete_count: `23`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1441 | 15 | -0.5126 | 0.0102 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 195 | 24 | -0.9728 | 0.1576 | `pass` | `NO_CHANGE` | False |
| `holding` | 34 | 23 | -1.0714 | 0.7882 | `pass` | `EXIT` | False |
| `scale_in` | 2303 | 2287 | -0.5857 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1319 | 33 | -0.9874 | 0.0728 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 65, 'complete_flow_count': 23, 'incomplete_flow_count': 3958, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1895 | 1879 | -0.7823 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 408 | 408 | 0.3198 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -0.8023 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:18b3144c7c` | 1 | 1 | 0.1192 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:98d4154191` | 1 | 1 | -0.8549 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:24854c19e5` | 1 | 1 | -1.3124 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:9d042ec94c` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3fde12b654` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:4b2fd7ef41` | 1 | 1 | -0.0805 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:47852c41fb` | 1 | 1 | -2.1939 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:827611b511` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:89a2d22c59` | 1 | 1 | -2.11 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.8 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:8c461a936f` | 1 | 1 | -0.62 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 1 | 1 | 0.0754 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 1 | 1 | -0.57 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a7c21066aa` | 1 | 1 | -1.36 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:583565312c` | 1 | 1 | 0.3289 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ccc234c442` | 1 | 1 | 0.5283 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 189, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1213 | 15 | -0.5126 | -1.0147 | 0.4667 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 676 | 13 | -0.6466 | -1.24 | 0.3846 | `hold_sample` |
| `stale_bucket` | `fresh` | 778 | 13 | -0.6466 | -1.24 | 0.3846 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 587 | 13 | -0.6466 | -1.24 | 0.3846 | `hold_sample` |
| `score_band` | `score_70p` | 125 | 11 | -0.6975 | -1.5136 | 0.2727 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 575 | 8 | -0.905 | -1.7425 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -0.5143 | 0.3686 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 225 | 6 | -0.1798 | -0.595 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 329 | 6 | -1.1396 | -2.1133 | 0.1667 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 704 | 5 | -0.0505 | -0.006 | 0.8 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.3157 | -1.46 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 419 | 4 | 0.1083 | -1.0425 | 0.5 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 284 | 4 | -1.0211 | -2.0575 | 0.25 | `source_quality_workorder` |
| `time_bucket` | `time_1400_close` | 443 | 4 | -0.6903 | 0.395 | 1.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -0.8366 | -3.5 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 3 | 0.0275 | -0.3433 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 295 | 3 | -0.4254 | -1.4667 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 619 | 2 | 0.3583 | 0.45 | 1.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 805 | 2 | 0.3583 | 0.45 | 1.0 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 739 | 2 | 0.3583 | 0.45 | 1.0 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 104, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 163 | 24 | -0.9728 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 38 | 24 | -0.9728 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 38 | 24 | -0.9728 | `keep_collecting` |
| `latency_state` | `simulated` | 38 | 24 | -0.9728 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 163 | 24 | -0.9728 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 38 | 24 | -0.9728 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 185 | 23 | -1.0303 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 29 | 17 | -0.5558 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 29 | 17 | -0.5558 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 25 | 16 | -0.6124 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 145 | 16 | -0.6124 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 25 | 16 | -0.6124 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 25 | 15 | -0.9529 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 14 | 11 | -1.2798 | `keep_collecting` |
| `would_limit_fill` | `false` | 173 | 11 | -0.7097 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 20 | 11 | -0.6392 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 13 | 9 | -1.006 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 13 | 8 | -1.6935 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 34 | 8 | -1.6935 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 13 | 8 | -1.6935 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 10 | 7 | -1.9855 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 8 | 7 | -1.9855 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 7 | -0.6839 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 9 | 7 | -1.9855 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 9 | 5 | -0.3983 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 9 | 5 | -0.3983 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 4 | -0.7549 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 4 | -1.596 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.5046 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 4 | 2 | -1.1191 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 5 | 1 | 0.3506 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_block|revalidation=warning_stale_context_or_quote|quote_consistency_stale|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.3506 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote|quote_consistency_stale` | 5 | 1 | 0.3506 | `keep_collecting` |
| `latency_state` | `caution` | 31 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 31 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 21, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 33 | 23 | -1.0714 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 33 | 23 | -1.0714 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 20 | 14 | -0.6673 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 13 | 12 | -1.8008 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 13 | 9 | -1.6999 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -0.1672 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.1232 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.1041 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -2.4976 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | -0.3212 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 22 | 22 | -1.0241 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 18 | 18 | -1.5118 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | -0.2756 | `hold_no_edge` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 10 | 10 | -0.847 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 9 | 9 | -1.3754 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 9 | 9 | -0.6591 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -0.1672 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -2.4976 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 6 | 6 | -1.0217 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.9029 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 5 | 5 | -0.1471 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 4 | 4 | -1.0554 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 4 | 4 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.5017 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.0275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.8023 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.6458 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.0513 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.7957 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -1.5825 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -1.5825 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -1.5825 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -1.5825 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.8549 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 0.7356 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1286 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 1286 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 1286 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 1286 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 1286 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 152, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2303 | 2287 | None | -0.6412 | 0.1732 | `hold_sample` |
| `qty_reason` | `qty_none` | 2287 | 2287 | None | -0.6412 | 0.1732 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2303 | 2287 | None | -0.6412 | 0.1732 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2278 | 2278 | None | -0.6465 | 0.1699 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1895 | 1879 | None | -0.8462 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1895 | 1879 | None | -0.8462 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1400 | 1400 | None | -0.4952 | 0.2714 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1338 | 1322 | None | -0.4999 | 0.2996 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1241 | 1241 | None | -0.6295 | 0.1966 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1094 | 1094 | None | -1.1236 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 982 | 966 | None | -0.8336 | 0.001 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 875 | 875 | None | -0.8628 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 765 | 765 | None | -0.4701 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 642 | 642 | None | -0.5903 | 0.1947 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 481 | 481 | None | -0.939 | 0.0041 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 431 | 431 | None | 0.1885 | 0.8817 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 420 | 420 | None | 0.2731 | 0.9238 | `hold_sample` |
| `arm` | `PYRAMID` | 408 | 408 | None | 0.303 | 0.9706 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 408 | 408 | None | 0.303 | 0.9706 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 387 | 387 | None | 0.2946 | 0.9716 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 0 | None | None | None | `hold_sample` |
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
