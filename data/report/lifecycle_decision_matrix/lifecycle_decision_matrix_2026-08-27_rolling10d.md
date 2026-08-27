# Lifecycle Decision Matrix - 2026-08-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-27_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `19665`
- source_rows_total: `24724`
- retained_rows: `19665`
- dropped_rows_by_source: `{}`
- joined_rows: `9788`
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
- lifecycle_flow_bucket_count: `161`
- lifecycle_flow_complete_count: `109`
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
| `entry` | 5382 | 61 | -0.4232 | 0.014 | `pass` | `NO_CHANGE` | False |
| `submit` | 646 | 127 | -0.8553 | 0.4174 | `pass` | `NO_CHANGE` | False |
| `holding` | 161 | 125 | -0.9292 | 0.9382 | `pass` | `EXIT` | False |
| `scale_in` | 9334 | 9266 | -0.8697 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4142 | 209 | -0.9062 | 0.3906 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 161, 'complete_flow_count': 109, 'incomplete_flow_count': 14605, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8479 | 8412 | -0.9974 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 854 | 853 | 0.3896 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 5 | 5 | -1.034 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 4 | 4 | -0.9775 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.26 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 2 | 2 | -0.845 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 2 | 2 | -1.365 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d8bc4e1490` | 2 | 2 | 0.2158 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:27b40f1c54` | 2 | 2 | -0.755 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 2 | 2 | -0.995 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 2 | 2 | -2.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:bbe961df76` | 2 | 2 | -0.985 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6669d1917b` | 2 | 2 | -1.3 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 326, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4427 | 59 | -0.357 | -1.068 | 0.3729 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2447 | 57 | -0.3821 | -1.1212 | 0.3509 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 2092 | 57 | -0.3821 | -1.1212 | 0.3509 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 2910 | 56 | -0.3768 | -1.1129 | 0.3571 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 2108 | 40 | -0.529 | -1.3337 | 0.275 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 1520 | 33 | -0.3391 | -1.2197 | 0.303 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 669 | 28 | -0.0442 | -1.026 | 0.25 | `hold_sample` |
| `score_band` | `score_70p` | 383 | 27 | -0.4963 | -1.2326 | 0.2592 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 26 | 26 | -0.223 | -1.5211 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | -0.6477 | 0.4865 | 0.913 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1223 | 22 | -0.4886 | -1.6987 | 0.3182 | `hold_sample` |
| `score_band` | `score_63_65` | 131 | 21 | -0.4843 | -0.7943 | 0.4762 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1126 | 12 | -0.1969 | -1.4658 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 2377 | 11 | 0.016 | -0.1182 | 0.7273 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -0.4489 | -3.373 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 26 | 9 | -0.0178 | -0.9266 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 4847 | 9 | -0.1951 | -1.0833 | 0.4444 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 593 | 8 | -0.0101 | -1.045 | 0.375 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 1133 | 8 | -0.7051 | -1.0513 | 0.125 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 1603 | 8 | -0.8278 | 0.2013 | 0.875 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 123, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 570 | 127 | -0.8553 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 158 | 127 | -0.8553 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 158 | 127 | -0.8553 | `keep_collecting` |
| `latency_state` | `simulated` | 158 | 127 | -0.8553 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 570 | 127 | -0.8553 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 622 | 125 | -0.8733 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 150 | 119 | -0.8289 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 113 | 88 | -0.8882 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 98 | 72 | -0.4267 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 98 | 72 | -0.4267 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 89 | 68 | -0.7321 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 86 | 64 | -0.4045 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 478 | 64 | -0.4045 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 86 | 64 | -0.4045 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 72 | 63 | -1.3133 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 72 | 63 | -1.3133 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 64 | 55 | -1.4165 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 59 | 55 | -1.4165 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 60 | 55 | -1.4165 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 119 | 53 | -1.3108 | `keep_collecting` |
| `would_limit_fill` | `false` | 546 | 44 | -0.44 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 42 | 36 | -0.7772 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 44 | 35 | -0.4396 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 37 | 31 | -0.6605 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 28 | 26 | -1.8657 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 25 | 21 | -1.3441 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 28 | 20 | -0.3264 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 28 | 20 | -0.3264 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 19 | -1.0651 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 19 | 10 | -1.3265 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 9 | -0.4415 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 8 | 8 | -1.2491 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 8 | 8 | -1.2491 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 6 | 6 | -0.8952 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 6 | -1.3202 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 151 | 125 | -0.9292 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 151 | 125 | -0.9292 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 101 | 83 | -0.9802 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 70 | 64 | -1.4691 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 47 | 47 | -1.3202 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 49 | 41 | -0.8435 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 36 | 35 | -0.4751 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 21 | 21 | -0.4397 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.8806 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 13 | 13 | -0.5534 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 12 | 9 | -0.8482 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2443 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -1.4322 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | -0.6689 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 0.0856 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.1182 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 1.7663 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | -0.179 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 0.2903 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 18 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 120 | 120 | -0.907 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 114 | 114 | -1.315 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 79 | 79 | -0.9068 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 57 | 57 | -0.349 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 48 | 48 | -1.141 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 44 | 44 | -0.813 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 42 | 42 | -0.5962 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 40 | 40 | -1.4673 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 36 | 36 | -0.3996 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 36 | 36 | -0.4606 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 31 | 31 | -0.5442 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 30 | 30 | -1.9593 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 28 | 28 | -0.9468 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 18 | 18 | -0.8602 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.5204 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 15 | 15 | -0.8386 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -1.3014 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 13 | 13 | -0.3167 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 10 | 10 | -0.8918 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.8918 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2443 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | -0.0136 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 8 | 8 | 0.5696 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -3.0391 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -1.8829 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 6 | 6 | -1.3075 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -1.3825 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | -0.5704 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.6829 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -1.0385 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 3 | 3 | 0.3314 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 1.2699 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 2 | 2 | -0.7522 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 2 | 2 | -2.1641 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 1.6569 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.6301 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 0.2903 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 392, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 9245 | 9245 | None | -0.9601 | 0.0872 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8480 | 8413 | None | -1.0888 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8382 | 8315 | None | -1.0644 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 7833 | 7779 | None | -0.8679 | 0.0982 | `hold_sample` |
| `qty_reason` | `qty_none` | 7780 | 7779 | None | -0.8679 | 0.0982 | `hold_sample` |
| `time_bucket` | `time_unknown` | 4963 | 4927 | None | -0.7456 | 0.1417 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 4914 | 4914 | None | -0.9724 | 0.0951 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4264 | 4264 | None | -0.8209 | 0.1417 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4166 | 4166 | None | -1.3921 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 3631 | 3576 | None | -0.9916 | 0.0008 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 3011 | 3011 | None | -1.0687 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2818 | 2782 | None | -0.6133 | 0.2511 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2681 | 2681 | None | -0.4504 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2209 | 2209 | None | -0.9028 | 0.1213 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1889 | 1889 | None | -1.0344 | 0.0407 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 1123 | 1123 | None | -0.0717 | 0.618 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1061 | 1061 | None | -0.8217 | 0.0603 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 1021 | 1021 | None | -0.782 | 0.0274 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 875 | 875 | None | 0.1911 | 0.8092 | `hold_sample` |
| `arm` | `PYRAMID` | 854 | 853 | None | 0.3624 | 0.9695 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `stage` | `exit` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.8918 | -1.189 | 0.1 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.9958 | -1.3278 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.3075 | -1.7434 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.3075 | -1.7434 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.26 | -1.68 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.6581 | -0.8775 | 0.25 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.3725 | -0.4967 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.045 | 0.06 | 1.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 10 | 0 | None | None | None | `hold_sample` |

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
