# Lifecycle Decision Matrix - 2026-08-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-21_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `9310`
- source_rows_total: `11601`
- retained_rows: `9310`
- dropped_rows_by_source: `{}`
- joined_rows: `4104`
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
- lifecycle_flow_complete_count: `50`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0074`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2780 | 29 | -0.5401 | 0.0156 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 350 | 60 | -0.9963 | 0.3921 | `pass` | `NO_CHANGE` | False |
| `holding` | 72 | 58 | -1.1707 | 0.916 | `pass` | `EXIT` | False |
| `scale_in` | 3896 | 3866 | -0.8595 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2212 | 91 | -1.0871 | 0.2003 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 50, 'incomplete_flow_count': 6738, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3422 | 3392 | -1.0314 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 474 | 474 | 0.3713 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:9d042ec94c` | 1 | 1 | -1.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3fde12b654` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:4b2fd7ef41` | 1 | 1 | -0.0805 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:47852c41fb` | 1 | 1 | -2.1939 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:827611b511` | 1 | 1 | -1.05 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 263, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2291 | 28 | -0.5389 | -1.0439 | 0.3928 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1298 | 26 | -0.608 | -1.1589 | 0.3461 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 1550 | 26 | -0.608 | -1.1589 | 0.3461 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 1128 | 26 | -0.608 | -1.1589 | 0.3461 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 1124 | 19 | -0.6968 | -1.3137 | 0.3158 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_normal` | 376 | 14 | -0.1601 | -0.9643 | 0.2857 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 814 | 14 | -0.2929 | -1.0064 | 0.3571 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 13 | 13 | -0.1822 | -1.4769 | 0.0 | `hold_sample` |
| `score_band` | `score_70p` | 180 | 12 | -0.628 | -1.6808 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | -0.9932 | 0.52 | 1.0 | `hold_sample` |
| `score_band` | `score_63_65` | 71 | 10 | -0.9128 | -0.444 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 641 | 8 | -0.8371 | -2.4163 | 0.125 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1283 | 6 | -0.0804 | -0.24 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 538 | 6 | -0.6965 | -1.85 | 0.1667 | `source_quality_workorder` |
| `time_bucket` | `time_1400_close` | 818 | 6 | -1.0177 | -0.1733 | 0.8333 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -0.4738 | -3.43 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |
| `score_band` | `score_lt60` | 2518 | 4 | 0.2996 | -0.925 | 0.5 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1548 | 3 | 0.0482 | -0.1667 | 0.6667 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1418 | 3 | 0.0482 | -0.1667 | 0.6667 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 118, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 304 | 60 | -0.9963 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 76 | 60 | -0.9963 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 76 | 60 | -0.9963 | `keep_collecting` |
| `latency_state` | `simulated` | 76 | 60 | -0.9963 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 304 | 60 | -0.9963 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 335 | 58 | -1.04 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 74 | 58 | -0.9986 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 55 | 44 | -1.2404 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 49 | 35 | -0.4941 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 49 | 35 | -0.4941 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 43 | 33 | -0.9963 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 43 | 32 | -0.5911 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 262 | 32 | -0.5911 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 43 | 32 | -0.5911 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 33 | 28 | -1.4595 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 33 | 28 | -1.4595 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 28 | 25 | -1.6994 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 26 | 25 | -1.6994 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 27 | 25 | -1.6994 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 60 | 24 | -1.4126 | `keep_collecting` |
| `would_limit_fill` | `false` | 301 | 21 | -0.5883 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 22 | 19 | -0.5519 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 16 | -0.592 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 19 | 14 | -0.2387 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -2.308 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 11 | -0.5962 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 16 | 11 | -0.5962 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 10 | 7 | -2.3123 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 7 | -0.368 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 5 | -0.5767 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 7 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 6 | 2 | 0.2693 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote|quote_consistency_stale` | 6 | 2 | 0.2693 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 29, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 70 | 58 | -1.1707 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 70 | 58 | -1.1707 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 47 | 40 | -1.1408 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 34 | 33 | -1.6085 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 23 | 23 | -1.4345 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 18 | -0.6579 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 22 | 17 | -1.2984 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.6404 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -2.0085 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.7913 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.3366 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | -2.0329 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -2.0329 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -1.3247 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.6398 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 56 | 56 | -1.1645 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 55 | 55 | -1.4188 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 33 | 33 | -0.9603 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 33 | 33 | -0.9603 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 33 | 33 | -0.9603 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 24 | 24 | -0.5935 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -1.0274 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 22 | 22 | -1.1582 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 18 | 18 | -1.7887 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 18 | -0.6579 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 18 | 18 | -2.1617 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 16 | 16 | -0.6509 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 14 | 14 | -0.8613 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.7793 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 11 | 11 | -0.5645 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -0.8638 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 9 | 9 | -1.2448 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -1.6549 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.9577 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | -0.3698 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -3.4816 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.3366 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.5265 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -1.0088 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0088 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -1.0088 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.0275 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.6824 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 1 | 1 | -1.5825 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.435 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8555 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 2121 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 2121 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 2121 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 2121 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 285, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 3855 | 3855 | None | -0.9535 | 0.117 | `hold_sample` |
| `arm` | `AVG_DOWN` | 3422 | 3392 | None | -1.1305 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3360 | 3330 | None | -1.0926 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2396 | 2379 | None | -0.6584 | 0.1682 | `hold_sample` |
| `qty_reason` | `qty_none` | 2379 | 2379 | None | -0.6584 | 0.1682 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2396 | 2379 | None | -0.6584 | 0.1682 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1888 | 1888 | None | -0.9573 | 0.1388 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1402 | 1402 | None | -0.5002 | 0.271 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1391 | 1374 | None | -0.5261 | 0.2911 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1151 | 1151 | None | -1.1442 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1069 | 1069 | None | -0.9316 | 0.1431 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1023 | 1006 | None | -0.8381 | 0.001 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 907 | 907 | None | -0.8891 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 796 | 796 | None | -0.4677 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 498 | 498 | None | -0.9281 | 0.006 | `hold_sample` |
| `arm` | `PYRAMID` | 474 | 474 | None | 0.3538 | 0.9747 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 474 | 474 | None | 0.3538 | 0.9747 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 472 | 472 | None | -0.8342 | 0.0296 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 451 | 451 | None | 0.1567 | 0.8514 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 430 | 430 | None | 0.3159 | 0.9744 | `hold_sample` |

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
