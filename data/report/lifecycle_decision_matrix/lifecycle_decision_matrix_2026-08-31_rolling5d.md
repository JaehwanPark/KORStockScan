# Lifecycle Decision Matrix - 2026-08-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-31_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `5205`
- source_rows_total: `6197`
- retained_rows: `5205`
- dropped_rows_by_source: `{}`
- joined_rows: `2717`
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
- lifecycle_flow_bucket_count: `69`
- lifecycle_flow_complete_count: `27`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0079`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1983 | 14 | -0.496 | 0.005 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 205 | 30 | -1.2171 | 0.1481 | `pass` | `NO_CHANGE` | False |
| `holding` | 42 | 30 | -1.0 | 0.7286 | `pass` | `EXIT` | False |
| `scale_in` | 2632 | 2599 | -0.6375 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 343 | 44 | -0.9522 | 0.4931 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 69, 'complete_flow_count': 27, 'incomplete_flow_count': 3389, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2211 | 2180 | -0.8482 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 421 | 419 | 0.4588 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -0.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.249 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a9d1313d5d` | 1 | 1 | 0.1763 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:d7ad29dfc9` | 1 | 1 | -0.44 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:61bcc9f24b` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:2a1b39688d` | 1 | 1 | -2.3901 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c918fe4c6d` | 1 | 1 | -1.693 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0953a2ca90` | 1 | 1 | -1.4345 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5f1ed96255` | 1 | 1 | 0.529 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 1 | 1 | 0.3563 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2f0e6b68fc` | 1 | 1 | -2.7606 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a74ce3066d` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:57240f2428` | 1 | 1 | -1.8805 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 1 | 1 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ffc82782b8` | 1 | 1 | 1.5492 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 229, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 862 | 13 | -0.5435 | -0.9269 | 0.3846 | `hold_sample` |
| `stale_bucket` | `fresh` | 1025 | 13 | -0.5435 | -0.9269 | 0.3846 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 731 | 13 | -0.5435 | -0.9269 | 0.3846 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1660 | 13 | -0.5435 | -0.9269 | 0.3846 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 564 | 10 | -0.0617 | -1.323 | 0.3 | `hold_sample` |
| `score_band` | `score_63_65` | 52 | 9 | -0.1686 | -0.5933 | 0.4445 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 259 | 7 | -0.063 | -1.0114 | 0.2857 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 759 | 7 | 0.0528 | -1.5629 | 0.2857 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | -0.6758 | 0.63 | 1.0 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.3137 | -1.496 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 5 | -0.2285 | -1.128 | 0.2 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 835 | 4 | -1.9454 | -0.0675 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 175 | 3 | -2.1493 | 0.3933 | 0.6667 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 421 | 3 | -0.0589 | -2.05 | 0.3333 | `hold_sample` |
| `score_band` | `score_70p` | 84 | 3 | -2.0426 | -1.5833 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -0.1289 | -3.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 2 | 2 | 0.1237 | -1.185 | 0.5 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 232 | 2 | 0.1734 | -0.42 | 0.5 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 441 | 2 | -2.2599 | 0.29 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 685 | 2 | -0.9033 | 0.56 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 106, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 191 | 30 | -1.2171 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 193 | 30 | -1.2171 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 43 | 30 | -1.2171 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 43 | 30 | -1.2171 | `keep_collecting` |
| `latency_state` | `simulated` | 43 | 30 | -1.2171 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 191 | 30 | -1.2171 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 41 | 29 | -1.2536 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 42 | 29 | -1.2536 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 35 | 23 | -1.039 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 17 | 16 | -1.8481 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 19 | 16 | -1.8481 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 16 | 16 | -1.8481 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 17 | 16 | -1.8481 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 19 | 16 | -1.8481 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 26 | 14 | -0.496 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 24 | 14 | -0.496 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 165 | 14 | -0.496 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 24 | 14 | -0.496 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 26 | 14 | -0.496 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 25 | 12 | -2.0013 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -2.0013 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 178 | 8 | -0.7954 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 16 | 8 | -0.7954 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 7 | 6 | -1.526 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 6 | -0.0967 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 8 | 6 | -0.0967 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 11 | 4 | -1.3881 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -1.7982 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | -3.46 | `keep_collecting` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 1 | 1 | -0.1581 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -0.1581 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 1 | 1 | -0.1581 | `keep_collecting` |
| `latency_state` | `caution` | 13 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 13 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 141 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 40 | 30 | -1.0 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 40 | 30 | -1.0 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 39 | 29 | -0.9761 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 15 | 14 | -1.6196 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 14 | 14 | -1.6196 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.696 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.5852 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -1.1288 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -1.1288 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -1.693 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | 0.9211 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | 0.9211 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -1.693 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 30 | 30 | -1.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 25 | 25 | -1.3403 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.5498 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 12 | 12 | -0.9167 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 12 | 12 | -0.9167 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 12 | 12 | -0.9167 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 11 | 11 | -1.6414 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 11 | 11 | -0.8961 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.696 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 10 | 10 | -1.006 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | -0.2608 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 7 | 7 | -2.3471 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 6 | 6 | -0.8611 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | -0.4308 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.0366 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.2643 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 3 | 3 | 0.3239 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.5199 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.6546 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.873 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -0.45 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | -1.1288 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.45 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 2 | 2 | -0.47 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.3447 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 2 | 2 | -2.1122 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.2887 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.0753 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -0.7725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9175 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.0785 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | 0.9211 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.8469 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.5215 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.5492 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | -0.7361 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 299 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 299 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 299 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 261, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2630 | 2599 | None | -0.7105 | 0.1602 | `hold_sample` |
| `qty_reason` | `qty_none` | 2601 | 2599 | None | -0.7105 | 0.1602 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2632 | 2599 | None | -0.7105 | 0.1602 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2589 | 2588 | None | -0.7186 | 0.1576 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2211 | 2180 | None | -0.9275 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2188 | 2157 | None | -0.9036 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1518 | 1485 | None | -0.5509 | 0.2806 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1262 | 1262 | None | -0.6831 | 0.1902 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1219 | 1219 | None | -1.388 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1152 | 1119 | None | -0.9165 | 0.0018 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 917 | 917 | None | -0.7813 | 0.1352 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 867 | 867 | None | -0.6192 | 0.2457 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 827 | 827 | None | -0.3879 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 717 | 717 | None | -0.9641 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 707 | 707 | None | -0.3077 | 0.5063 | `hold_sample` |
| `ai_score_source` | `live` | 587 | 587 | None | -0.6401 | 0.2385 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 518 | 518 | None | -0.7288 | 0.112 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 505 | 505 | None | 0.1646 | 0.7327 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 446 | 446 | None | -1.1159 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 421 | 419 | None | 0.4234 | 0.9976 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 19, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.45 | -0.6 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -0.7725 | -1.03 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7725 | -1.03 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -0.7725 | -1.03 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.1275 | -0.17 | 0.0 | `hold_sample` |
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
