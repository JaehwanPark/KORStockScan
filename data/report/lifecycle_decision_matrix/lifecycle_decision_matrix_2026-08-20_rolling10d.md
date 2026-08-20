# Lifecycle Decision Matrix - 2026-08-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-20_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `14593`
- source_rows_total: `17439`
- retained_rows: `14593`
- dropped_rows_by_source: `{}`
- joined_rows: `6544`
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
- lifecycle_flow_bucket_count: `123`
- lifecycle_flow_complete_count: `59`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0055`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4398 | 42 | -0.3965 | 0.0125 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 503 | 80 | -0.7838 | 0.3503 | `pass` | `NO_CHANGE` | False |
| `holding` | 115 | 78 | -0.9792 | 0.8041 | `pass` | `EXIT` | False |
| `scale_in` | 6299 | 6237 | -0.8254 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3278 | 107 | -0.8623 | 0.1788 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 123, 'complete_flow_count': 59, 'incomplete_flow_count': 10624, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5780 | 5718 | -0.9313 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 519 | 519 | 0.3423 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 4 | 4 | -0.842 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.7675 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1230ecd40d` | 1 | 1 | -0.0415 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:18b3144c7c` | 1 | 1 | 0.1192 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:a43861edf2` | 1 | 1 | -0.73 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:f2f4676367` | 1 | 1 | 0.1639 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 313, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3524 | 34 | -0.3849 | -0.9977 | 0.3823 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2364 | 33 | -0.3812 | -1.0452 | 0.3636 | `hold_sample` |
| `stale_bucket` | `fresh` | 2598 | 33 | -0.3812 | -1.0452 | 0.3636 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2034 | 33 | -0.3812 | -1.0452 | 0.3636 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1955 | 25 | -0.3617 | -0.9624 | 0.4 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1193 | 23 | -0.2554 | -1.0296 | 0.3043 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 22 | 22 | -0.1533 | -1.4714 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 239 | 20 | -0.3622 | -1.2815 | 0.35 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 676 | 19 | -0.1441 | -1.0295 | 0.2632 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.9581 | 0.5614 | 1.0 | `hold_sample` |
| `score_band` | `score_63_65` | 186 | 13 | -0.785 | -0.7577 | 0.3077 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 2246 | 9 | -0.4528 | -1.1255 | 0.2222 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1990 | 9 | -0.4528 | -1.1255 | 0.2222 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 1139 | 9 | -0.4178 | -1.6078 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 1507 | 9 | -0.4528 | -1.1255 | 0.2222 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 162 | 8 | -0.4456 | -1.3375 | 0.125 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 134 | 8 | -0.4456 | -1.3375 | 0.125 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 134 | 8 | -0.4456 | -1.3375 | 0.125 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 966 | 8 | -0.1178 | -1.5262 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | 0.0222 | -3.3517 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 121, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 460 | 80 | -0.7838 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 113 | 80 | -0.7838 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 113 | 80 | -0.7838 | `keep_collecting` |
| `latency_state` | `simulated` | 113 | 80 | -0.7838 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 460 | 80 | -0.7838 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 489 | 78 | -0.8108 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 111 | 78 | -0.7801 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 87 | 55 | -1.0512 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 74 | 52 | -0.801 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 75 | 47 | -0.3407 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 75 | 47 | -0.3407 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 70 | 44 | -0.4007 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 403 | 44 | -0.4007 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 70 | 44 | -0.4007 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 43 | 36 | -1.252 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 41 | 35 | -1.2218 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 43 | 33 | -1.4149 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 37 | 33 | -1.4149 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 38 | 33 | -1.4149 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 74 | 32 | -1.1909 | `keep_collecting` |
| `would_limit_fill` | `false` | 439 | 30 | -0.4138 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 27 | 23 | -0.1318 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 37 | 22 | -0.489 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 27 | 20 | -0.3157 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 18 | -1.8393 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 21 | 14 | -0.3727 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 18 | 11 | -0.4912 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -0.368 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 12 | 8 | -0.2071 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 11 | 7 | -2.073 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 7 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 3 | 0.0621 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 5 | 2 | 0.2693 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 108 | 78 | -0.9792 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 108 | 78 | -0.9792 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 77 | 56 | -1.0587 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 47 | 44 | -1.343 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 36 | 36 | -1.2777 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 30 | 21 | -0.8042 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 21 | 21 | -0.72 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.7558 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.734 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -1.637 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 6 | -0.9845 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.9845 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.3299 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.8284 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -0.4178 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 30 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 21 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 3 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 73 | 73 | -0.8165 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 62 | 62 | -1.2707 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 33 | 33 | -0.6666 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 32 | 32 | -0.237 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 27 | 27 | -0.9708 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 24 | 24 | -0.7947 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 22 | 22 | -1.3037 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 21 | 21 | -0.72 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 18 | 18 | -0.496 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 18 | 18 | -1.1922 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 17 | 17 | -1.9382 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 17 | 17 | -0.8265 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 15 | 15 | -0.6849 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 12 | 12 | -1.1125 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.5278 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.4848 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -1.9287 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 7 | 7 | -0.3735 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | 0.3299 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.2869 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.4055 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.1332 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.0186 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.4565 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.1401 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.4219 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 3171 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 305, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 6229 | 6229 | None | -0.9095 | 0.0795 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5780 | 5718 | None | -1.0195 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5714 | 5652 | None | -0.9942 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 4799 | 4750 | None | -0.7496 | 0.0926 | `hold_sample` |
| `qty_reason` | `qty_none` | 4750 | 4750 | None | -0.7496 | 0.0926 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4799 | 4750 | None | -0.7496 | 0.0926 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3182 | 3182 | None | -0.8926 | 0.1056 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2726 | 2726 | None | -1.0831 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2577 | 2577 | None | -0.747 | 0.1389 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2624 | 2575 | None | -0.6648 | 0.1709 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2228 | 2179 | None | -0.8483 | 0.0014 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1829 | 1829 | None | -0.8698 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1631 | 1631 | None | -0.9786 | 0.0656 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1497 | 1497 | None | -0.4867 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1154 | 1154 | None | -0.7688 | 0.0347 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 727 | 727 | None | -0.1821 | 0.5819 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 677 | 677 | None | -0.7831 | 0.0221 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 664 | 664 | None | -0.7393 | 0.0497 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 622 | 622 | None | -0.9266 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_3` | 553 | 553 | None | -0.8136 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 14 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 7 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 14 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `stage` | `exit` | 7 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 14 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.9214 | -1.2286 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -1.221 | -1.628 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2869 | -0.3825 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2869 | -0.3825 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | -2.3567 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.2375 | -0.3167 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.7675 | -2.3567 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -1.7675 | -2.3567 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
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
