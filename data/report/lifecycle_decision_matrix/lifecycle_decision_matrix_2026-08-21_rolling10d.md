# Lifecycle Decision Matrix - 2026-08-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-21_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `16694`
- source_rows_total: `20400`
- retained_rows: `16694`
- dropped_rows_by_source: `{}`
- joined_rows: `7179`
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
- lifecycle_flow_bucket_count: `133`
- lifecycle_flow_complete_count: `67`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4634 | 44 | -0.4141 | 0.0122 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 568 | 87 | -0.8751 | 0.3332 | `pass` | `NO_CHANGE` | False |
| `holding` | 126 | 85 | -1.0412 | 0.8114 | `pass` | `EXIT` | False |
| `scale_in` | 6901 | 6839 | -0.8186 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4465 | 124 | -0.9102 | 0.1554 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 133, 'complete_flow_count': 67, 'incomplete_flow_count': 12457, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6269 | 6207 | -0.9365 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 632 | 632 | 0.3398 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 4 | 4 | -0.9565 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 3 | 3 | -0.8214 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 3 | 3 | -0.9233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f658be39ac` | 3 | 3 | -1.7675 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:305d9e5c71` | 3 | 3 | -0.2375 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:5c4d0773e1` | 2 | 2 | -1.0275 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:5603187fa1` | 2 | 2 | 4.0844 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:18b3144c7c` | 1 | 1 | 0.1192 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:a43861edf2` | 1 | 1 | -0.73 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:f2f4676367` | 1 | 1 | 0.1639 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f548b6989d` | 1 | 1 | -0.34 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:927a4c8e9e` | 1 | 1 | -0.2151 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 308, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3776 | 39 | -0.3963 | -1.0364 | 0.4102 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2280 | 37 | -0.4371 | -1.1168 | 0.3784 | `hold_sample` |
| `stale_bucket` | `fresh` | 2630 | 37 | -0.4371 | -1.1168 | 0.3784 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1970 | 37 | -0.4371 | -1.1168 | 0.3784 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1912 | 27 | -0.4408 | -1.1637 | 0.3704 | `hold_sample` |
| `score_band` | `score_70p` | 296 | 22 | -0.4593 | -1.4995 | 0.3182 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1248 | 22 | -0.251 | -1.0105 | 0.3182 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 646 | 20 | -0.1491 | -0.958 | 0.3 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 20 | 20 | -0.1793 | -1.476 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 16 | 16 | -0.7442 | 0.4819 | 1.0 | `hold_sample` |
| `score_band` | `score_63_65` | 146 | 13 | -0.7363 | -0.683 | 0.3846 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1123 | 11 | -0.6019 | -1.9845 | 0.2727 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1045 | 10 | -0.3803 | -1.957 | 0.2 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | -0.3409 | -3.4337 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 1488 | 8 | -0.7338 | -0.0075 | 0.875 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 2528 | 7 | -0.2927 | -1.1371 | 0.2857 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 2056 | 7 | -0.0003 | -0.7614 | 0.5714 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 2296 | 7 | -0.2927 | -1.1371 | 0.2857 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 1688 | 7 | -0.2927 | -1.1371 | 0.2857 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 25 | 6 | 0.0115 | -0.64 | 0.5 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 507 | 87 | -0.8751 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 126 | 87 | -0.8751 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 126 | 87 | -0.8751 | `keep_collecting` |
| `latency_state` | `simulated` | 126 | 87 | -0.8751 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 507 | 87 | -0.8751 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 550 | 85 | -0.902 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 124 | 85 | -0.8738 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 96 | 61 | -1.0629 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 77 | 51 | -0.7963 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 82 | 50 | -0.3719 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 82 | 50 | -0.3719 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 76 | 47 | -0.4301 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 442 | 47 | -0.4301 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 76 | 47 | -0.4301 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 50 | 40 | -1.398 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 48 | 39 | -1.3746 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 49 | 37 | -1.5551 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 42 | 37 | -1.5551 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 44 | 37 | -1.5551 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 92 | 36 | -1.3599 | `keep_collecting` |
| `would_limit_fill` | `false` | 497 | 34 | -0.4276 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 34 | 26 | -0.7132 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 31 | 24 | -0.3933 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 39 | 24 | -0.4175 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 25 | 21 | -1.9344 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 21 | 13 | -0.4365 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 20 | 12 | -0.4706 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 11 | -0.6374 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 16 | 10 | -0.4517 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 14 | 9 | -1.861 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 8 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 7 | 2 | 0.2693 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote|quote_consistency_stale` | 7 | 2 | 0.2693 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 119 | 85 | -1.0412 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 119 | 85 | -1.0412 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 80 | 57 | -1.0418 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 49 | 46 | -1.5035 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 34 | 34 | -1.3139 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 38 | 27 | -1.0713 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 26 | 26 | -0.591 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 14 | 14 | -0.5655 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 12 | 12 | -2.0408 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.659 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 6 | -0.9845 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.9845 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.0329 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.8284 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | -1.3247 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.3289 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 34 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
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
| `exit_source_stage` | `sim_post_sell_evaluation` | 80 | 80 | -0.8967 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 70 | 70 | -1.3569 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 37 | 37 | -0.9373 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 37 | 37 | -0.9373 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 37 | 37 | -0.9373 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 37 | 37 | -0.2607 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 35 | 35 | -0.6248 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 26 | 26 | -0.591 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 25 | 25 | -1.5198 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 24 | 24 | -1.1496 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 22 | 22 | -0.8067 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 21 | 21 | -2.1116 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 20 | 20 | -0.5937 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 19 | 19 | -0.6639 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 16 | 16 | -0.8217 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 13 | 13 | -0.5454 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -1.0429 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 10 | 10 | -0.3389 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.6107 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 7 | 7 | -0.9214 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -1.9287 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 5 | 5 | -0.0329 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -3.2695 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.2869 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.7675 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -1.1332 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.4003 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 3 | 3 | 0.5265 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.4565 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 2 | 2 | 1.0468 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | -0.7669 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300_plus` | 2 | 2 | 4.0844 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.3289 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg070_neg010` | 1 | 1 | -0.8911 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 4341 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 319, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 6823 | 6823 | None | -0.904 | 0.0862 | `hold_sample` |
| `arm` | `AVG_DOWN` | 6269 | 6207 | None | -1.0248 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 6203 | 6141 | None | -1.0016 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 5401 | 5352 | None | -0.7581 | 0.1011 | `hold_sample` |
| `qty_reason` | `qty_none` | 5352 | 5352 | None | -0.7581 | 0.1011 | `hold_sample` |
| `time_bucket` | `time_unknown` | 5401 | 5352 | None | -0.7581 | 0.1011 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 3388 | 3388 | None | -0.91 | 0.1012 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 3011 | 3011 | None | -1.1269 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2980 | 2931 | None | -0.6641 | 0.1846 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2900 | 2900 | None | -0.72 | 0.1576 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 2474 | 2425 | None | -0.8705 | 0.0012 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2069 | 2069 | None | -0.8961 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 1944 | 1944 | None | -0.8981 | 0.1034 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1691 | 1691 | None | -0.4842 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1331 | 1331 | None | -0.8346 | 0.0308 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 833 | 833 | None | -0.1342 | 0.617 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 731 | 731 | None | -0.786 | 0.0452 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 718 | 718 | None | -0.7781 | 0.0209 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 690 | 690 | None | -0.9692 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 636 | 636 | None | 0.2254 | 0.8302 | `hold_sample` |

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
