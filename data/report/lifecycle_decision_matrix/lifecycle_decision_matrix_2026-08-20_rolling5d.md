# Lifecycle Decision Matrix - 2026-08-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-20_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6684`
- source_rows_total: `8114`
- retained_rows: `6684`
- dropped_rows_by_source: `{}`
- joined_rows: `3441`
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
- lifecycle_flow_bucket_count: `83`
- lifecycle_flow_complete_count: `39`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0081`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2075 | 24 | -0.554 | 0.0181 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 256 | 50 | -0.9111 | 0.4492 | `pass` | `NO_CHANGE` | False |
| `holding` | 58 | 48 | -1.1335 | 0.958 | `pass` | `EXIT` | False |
| `scale_in` | 3275 | 3248 | -0.8813 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1020 | 71 | -1.0839 | 0.2472 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 83, 'complete_flow_count': 39, 'incomplete_flow_count': 4762, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2916 | 2889 | -1.0389 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 359 | 359 | 0.3867 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -1.115 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:18b3144c7c` | 1 | 1 | 0.1192 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:a43861edf2` | 1 | 1 | -0.73 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:98d4154191` | 1 | 1 | -0.8549 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:24854c19e5` | 1 | 1 | -1.3124 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:4b2fd7ef41` | 1 | 1 | -0.0805 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:47852c41fb` | 1 | 1 | -2.1939 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:89a2d22c59` | 1 | 1 | -2.11 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2a8b3a8336` | 1 | 1 | -0.39 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 244, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1698 | 23 | -0.5532 | -0.9883 | 0.3478 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1022 | 22 | -0.5552 | -1.0591 | 0.3181 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 1202 | 22 | -0.5552 | -1.0591 | 0.3181 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 892 | 22 | -0.5552 | -1.0591 | 0.3181 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 872 | 17 | -0.6105 | -1.0353 | 0.3529 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 635 | 14 | -0.2929 | -1.0064 | 0.3571 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 326 | 13 | -0.1536 | -1.0692 | 0.2308 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | -0.1822 | -1.4769 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 118 | 10 | -0.4676 | -1.281 | 0.3 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 8 | 8 | -1.4273 | 0.6075 | 1.0 | `hold_sample` |
| `score_band` | `score_63_65` | 64 | 8 | -1.0494 | -0.6212 | 0.375 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 473 | 6 | -0.6394 | -1.995 | 0.1667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 404 | 4 | -0.3296 | -0.935 | 0.25 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 912 | 3 | -0.3252 | -0.7667 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | 0.1638 | -3.2633 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 3 | 0.0275 | -0.3433 | 0.6667 | `hold_sample` |
| `score_band` | `score_60_62` | 7 | 3 | -0.0653 | -0.7733 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 1882 | 3 | -0.0093 | -1.3433 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 215 | 3 | -0.4562 | -0.9433 | 0.3333 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 112, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 228 | 50 | -0.9111 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 60 | 50 | -0.9111 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 60 | 50 | -0.9111 | `keep_collecting` |
| `latency_state` | `simulated` | 60 | 50 | -0.9111 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 228 | 50 | -0.9111 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 245 | 48 | -0.9603 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 58 | 48 | -0.9103 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 46 | 38 | -1.2515 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 37 | 31 | -1.0684 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 40 | 30 | -0.4976 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 40 | 30 | -0.4976 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 35 | 27 | -0.6129 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 195 | 27 | -0.6129 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 35 | 27 | -0.6129 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 25 | 23 | -1.2611 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 25 | 23 | -1.2611 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 21 | 20 | -1.5313 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 20 | 20 | -1.5313 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 20 | 20 | -1.5313 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 41 | 19 | -1.1602 | `keep_collecting` |
| `would_limit_fill` | `false` | 217 | 17 | -0.6019 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 16 | 14 | -0.7292 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 15 | 13 | 0.1342 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 12 | 10 | 0.3864 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 10 | -0.6315 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -2.249 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 14 | 10 | -0.6315 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 7 | 5 | -2.7896 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | 0.3537 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 6 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 3 | -0.0077 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 4 | 2 | 0.2693 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote|quote_consistency_stale` | 4 | 2 | 0.2693 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 29, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 56 | 48 | -1.1335 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 56 | 48 | -1.1335 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 41 | 36 | -1.227 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 30 | 29 | -1.4374 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 23 | 23 | -1.4345 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | -0.892 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 14 | 11 | -0.9124 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.8979 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.4485 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -1.1047 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | -2.0329 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -2.0329 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.6398 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 46 | 46 | -1.1243 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 45 | 45 | -1.3446 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 19 | 19 | -1.1489 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.6746 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 16 | 16 | -1.2094 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 14 | 14 | -1.6316 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -0.8613 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | -1.9655 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 13 | 13 | -0.5421 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | -0.892 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -0.8638 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 9 | -0.8656 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 8 | 8 | -1.3745 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.5528 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -1.5228 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.9577 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | -0.4815 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -1.0088 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0088 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0088 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.0275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.6824 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.3174 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.4219 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -1.5825 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.435 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 949 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 949 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 949 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 949 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 949 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 260, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 3245 | 3245 | None | -0.9744 | 0.1097 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2916 | 2889 | None | -1.1397 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2854 | 2827 | None | -1.0952 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1775 | 1761 | None | -0.6012 | 0.1687 | `hold_sample` |
| `qty_reason` | `qty_none` | 1761 | 1761 | None | -0.6012 | 0.1687 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1775 | 1761 | None | -0.6012 | 0.1687 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1682 | 1682 | None | -0.9301 | 0.1516 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1079 | 1079 | None | -0.4988 | 0.2604 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1023 | 1009 | None | -0.4787 | 0.2944 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 856 | 856 | None | -1.0131 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 767 | 753 | None | -0.7642 | 0.0013 | `hold_sample` |
| `ai_score_source` | `live` | 752 | 752 | None | -1.1218 | 0.0785 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 663 | 663 | None | -0.8137 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 598 | 598 | None | -0.4691 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 419 | 419 | None | -0.8517 | 0.0286 | `hold_sample` |
| `arm` | `PYRAMID` | 359 | 359 | None | 0.3709 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 359 | 359 | None | 0.3709 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 340 | 340 | None | 0.1526 | 0.8559 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 322 | 322 | None | 0.3225 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 321 | 321 | None | -0.7431 | 0.0062 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 4 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0088 | -1.345 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 1 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2 | 1 | -1.5825 | -2.11 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
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
