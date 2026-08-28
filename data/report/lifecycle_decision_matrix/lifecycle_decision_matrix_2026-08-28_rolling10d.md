# Lifecycle Decision Matrix - 2026-08-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-28_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `18130`
- source_rows_total: `22571`
- retained_rows: `18130`
- dropped_rows_by_source: `{}`
- joined_rows: `9142`
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
- lifecycle_flow_bucket_count: `152`
- lifecycle_flow_complete_count: `99`
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
| `entry` | 5253 | 55 | -0.4464 | 0.0112 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 614 | 111 | -0.7916 | 0.3294 | `pass` | `NO_CHANGE` | False |
| `holding` | 149 | 110 | -0.8636 | 0.8953 | `pass` | `EXIT` | False |
| `scale_in` | 8748 | 8681 | -0.7719 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3366 | 185 | -0.8486 | 0.4694 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 152, 'complete_flow_count': 99, 'incomplete_flow_count': 13220, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 7838 | 7772 | -0.9034 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 909 | 908 | 0.3542 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 4 | 4 | -0.94 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.26 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 2 | 2 | -1.12 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -0.8023 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 2 | 2 | 0.2158 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 2 | 2 | -0.755 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 2 | 2 | -0.995 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -1.575 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 2 | 2 | -0.985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6669d1917b` | 2 | 2 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.249 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1793c3951c` | 1 | 1 | -0.6466 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:05c0ca21ce` | 1 | 1 | 0.045 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 313, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4326 | 54 | -0.3773 | -1.095 | 0.3704 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2425 | 52 | -0.4056 | -1.1544 | 0.3461 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 2081 | 52 | -0.4056 | -1.1544 | 0.3461 | `hold_sample` |
| `stale_bucket` | `fresh` | 2831 | 51 | -0.4001 | -1.1459 | 0.3529 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 2090 | 33 | -0.4575 | -1.4712 | 0.2424 | `hold_sample` |
| `score_band` | `score_70p` | 407 | 29 | -0.6587 | -1.181 | 0.2758 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1474 | 29 | -0.2643 | -1.3617 | 0.2759 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 680 | 25 | -0.0487 | -0.9776 | 0.28 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 22 | 22 | -0.2855 | -1.5268 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1227 | 21 | -0.5121 | -1.6305 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 21 | 21 | -0.5754 | 0.4005 | 0.9048 | `hold_sample` |
| `score_band` | `score_63_65` | 102 | 18 | -0.162 | -0.9639 | 0.4445 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 2272 | 13 | -0.5101 | -0.1777 | 0.6923 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1112 | 11 | -0.6281 | -1.3327 | 0.4545 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 9 | 9 | -0.4993 | -3.4 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 26 | 9 | -0.0178 | -0.9266 | 0.3333 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 569 | 8 | 0.1696 | -1.0337 | 0.375 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 1038 | 8 | -0.7051 | -1.0513 | 0.125 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 7 | -0.1657 | -1.01 | 0.2857 | `hold_sample` |
| `score_band` | `score_lt60` | 4726 | 7 | -0.3197 | -0.7357 | 0.5714 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 124, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 533 | 111 | -0.7916 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 146 | 111 | -0.7916 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 146 | 111 | -0.7916 | `keep_collecting` |
| `latency_state` | `simulated` | 146 | 111 | -0.7916 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 533 | 111 | -0.7916 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 589 | 110 | -0.802 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 140 | 105 | -0.7594 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 103 | 74 | -0.8008 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 93 | 63 | -0.4788 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 93 | 63 | -0.4788 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 82 | 57 | -0.5869 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 81 | 57 | -0.4221 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 450 | 57 | -0.4221 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 81 | 57 | -0.4221 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 65 | 54 | -1.1816 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 65 | 54 | -1.1816 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 57 | 48 | -1.2022 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 52 | 48 | -1.2022 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 53 | 48 | -1.2022 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 114 | 45 | -1.246 | `keep_collecting` |
| `would_limit_fill` | `false` | 522 | 38 | -0.5663 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 40 | 34 | -0.8726 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 37 | 31 | -0.6605 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 41 | 29 | -0.605 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 21 | -1.7514 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 23 | 19 | -1.1757 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 26 | 19 | -0.1338 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 19 | -1.0651 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 27 | 19 | -0.1338 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 20 | 9 | -0.8596 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 13 | 9 | -0.4415 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 6 | 6 | -1.3553 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 6 | 6 | -1.3553 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -1.2904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 5 | -0.4786 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 138 | 110 | -0.8636 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 138 | 110 | -0.8636 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 90 | 69 | -0.8755 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 62 | 55 | -1.4104 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 48 | 41 | -0.8435 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 38 | 38 | -1.2001 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 33 | 32 | -0.4513 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 19 | 19 | -0.3814 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.8806 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 13 | 13 | -0.5534 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 8 | -0.5185 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.3926 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.2676 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.9188 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | -0.6376 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 4 | 4 | -0.3341 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 1.7663 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 11 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 28 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 21 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 51, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 105 | 105 | -0.8352 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 99 | 99 | -1.2502 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 69 | 69 | -0.8638 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 69 | 69 | -0.8638 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 69 | 69 | -0.8638 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 51 | 51 | -0.2979 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 41 | 41 | -1.0805 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 38 | 38 | -1.3022 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 38 | 38 | -0.5259 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.7418 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 33 | 33 | -0.4363 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 31 | 31 | -0.3712 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 28 | 28 | -0.5464 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 24 | 24 | -0.9674 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 24 | 24 | -1.8562 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 17 | 17 | -0.8488 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 14 | 14 | -0.2814 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -1.4297 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 11 | 11 | -0.8809 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.8809 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 11 | 11 | -1.2786 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -0.8451 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 8 | 8 | -1.3731 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.3926 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | -0.2676 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 7 | 7 | -1.2311 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -0.6303 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.8875 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.5704 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 6 | 6 | 0.6188 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -2.9278 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -1.0385 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -1.2784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 2.3018 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 349, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 8746 | 8681 | None | -0.8458 | 0.1014 | `hold_sample` |
| `qty_reason` | `qty_none` | 8683 | 8681 | None | -0.8458 | 0.1014 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 8661 | 8661 | None | -0.8502 | 0.0995 | `hold_sample` |
| `arm` | `AVG_DOWN` | 7839 | 7773 | None | -0.9826 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 7799 | 7733 | None | -0.9714 | 0.0 | `hold_sample` |
| `time_bucket` | `time_unknown` | 5877 | 5829 | None | -0.7316 | 0.1397 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 4841 | 4841 | None | -0.8446 | 0.1112 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4669 | 4669 | None | -0.7958 | 0.1448 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4508 | 4508 | None | -1.3952 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 4049 | 3982 | None | -0.9706 | 0.0008 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3327 | 3279 | None | -0.6035 | 0.2485 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3277 | 3277 | None | -1.0479 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3043 | 3043 | None | -0.4383 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2169 | 2169 | None | -1.0033 | 0.0433 | `hold_sample` |
| `ai_score_source` | `live` | 2008 | 2008 | None | -0.7699 | 0.1325 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1351 | 1351 | None | -0.1022 | 0.5981 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1201 | 1201 | None | -0.8049 | 0.0733 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1070 | 1070 | None | 0.179 | 0.7682 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 912 | 912 | None | -1.0586 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 909 | 908 | None | 0.3275 | 0.9714 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 22 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 11 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 22 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `stage` | `exit` | 11 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 22 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 11 | 11 | -0.8809 | -1.1746 | 0.0909 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 20 | 10 | -0.9735 | -1.298 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 7 | 7 | -1.2311 | -1.6414 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 7 | -1.2311 | -1.6414 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.26 | -1.68 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.6581 | -0.8775 | 0.25 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.585 | -0.78 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 11 | 0 | None | None | None | `hold_sample` |

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
