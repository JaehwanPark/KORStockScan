# Lifecycle Decision Matrix - 2026-08-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-19_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4018`
- source_rows_total: `4901`
- retained_rows: `4018`
- dropped_rows_by_source: `{}`
- joined_rows: `1722`
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
- lifecycle_flow_complete_count: `27`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0096`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1339 | 14 | -0.5695 | 0.0214 | `pass` | `NO_CHANGE` | False |
| `submit` | 155 | 36 | -1.012 | 0.5484 | `pass` | `NO_CHANGE` | False |
| `holding` | 38 | 35 | -1.236 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 1593 | 1579 | -1.2559 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 893 | 58 | -1.1437 | 0.2728 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 65, 'complete_flow_count': 27, 'incomplete_flow_count': 2780, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1527 | 1513 | -1.3408 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 66 | 66 | 0.6896 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -1.115 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:03eec49aed` | 2 | 2 | -1.1106 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:77c2d7d131` | 2 | 2 | -1.195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bf44bd3042` | 1 | 1 | -0.53 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:92f69621e6` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:e2e349e4ea` | 1 | 1 | -1.2 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:53097ae10f` | 1 | 1 | -0.2008 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:a101f93752` | 1 | 1 | -1.17 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_bloc:a43861edf2` | 1 | 1 | -0.73 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2a8b3a8336` | 1 | 1 | -0.39 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a6d949bab9` | 1 | 1 | -1.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:4db4bab026` | 1 | 1 | -0.6724 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:2ee314bc27` | 1 | 1 | -0.63 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -2.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:63a0b8330e` | 1 | 1 | -2.6687 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a74ce3066d` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c03b274e24` | 1 | 1 | -0.58 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 212, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 622 | 13 | -0.5693 | -1.0777 | 0.3077 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 772 | 13 | -0.5693 | -1.0777 | 0.3077 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 541 | 13 | -0.5693 | -1.0777 | 0.3077 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1078 | 13 | -0.5693 | -1.0777 | 0.3077 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 549 | 11 | -0.5454 | -1.0018 | 0.3636 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 395 | 10 | -0.4534 | -0.992 | 0.3 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 151 | 8 | -0.1453 | -1.2412 | 0.125 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | -0.0987 | -1.4875 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 52 | 8 | -1.0494 | -0.6212 | 0.375 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | -0.3294 | -1.078 | 0.2 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | -1.8312 | 0.785 | 1.0 | `hold_sample` |
| `score_band` | `score_60_62` | 7 | 3 | -0.0653 | -0.7733 | 0.3333 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 143 | 2 | -3.0882 | 0.91 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 312 | 2 | 0.0703 | -3.325 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | 0.0703 | -3.325 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | 0.0037 | -1.535 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 1222 | 2 | 0.2409 | -2.3 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 254 | 2 | -0.0473 | -1.435 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_1400_close` | 375 | 2 | -1.6724 | -1.31 | 0.5 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 25 | 1 | -0.572 | -1.4 | 0.0 | `source_quality_workorder` |

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
| `actual_order_submitted` | `false` | 141 | 36 | -1.012 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 38 | 36 | -1.012 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 38 | 36 | -1.012 | `keep_collecting` |
| `latency_state` | `simulated` | 38 | 36 | -1.012 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 141 | 36 | -1.012 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 150 | 35 | -1.0463 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 36 | 34 | -1.0169 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 30 | 29 | -1.3891 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 23 | 22 | -1.1749 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 20 | 20 | -1.3659 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 20 | 20 | -1.3659 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 18 | 18 | -1.5881 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 20 | 18 | -0.4359 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 18 | 18 | -1.5881 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 18 | 18 | -1.5881 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 20 | 18 | -0.4359 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 18 | 16 | -0.5697 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 26 | 16 | -1.2721 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 117 | 16 | -0.5697 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 18 | 16 | -0.5697 | `keep_collecting` |
| `would_limit_fill` | `false` | 128 | 10 | -0.4548 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -2.249 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 9 | -0.5205 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 8 | 8 | 0.449 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 6 | -0.7612 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 7 | 6 | -0.7612 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 6 | 5 | -2.7896 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 6 | 5 | 1.1424 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 4 | -1.7409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -2.9104 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | 1.2693 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -0.9304 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 2 | 2 | -0.9304 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_0_5bps` | 1 | 1 | -0.2298 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_block` | 1 | 1 | 0.1881 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 37 | 35 | -1.236 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 37 | 35 | -1.236 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 27 | 26 | -1.3957 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 21 | 21 | -1.4985 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.5512 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -1.1485 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 9 | 8 | -0.8468 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -1.3644 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.2749 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -1.1047 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 3 | 2 | -2.0329 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -2.0329 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | -0.2008 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.2008 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.794 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.6398 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 37 | 37 | -1.3735 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 34 | 34 | -1.2553 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 23 | 23 | -1.0096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 16 | 16 | -1.2094 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 13 | 13 | -1.2824 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | -0.8625 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 12 | 12 | -0.516 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 12 | 12 | -1.9938 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 9 | 9 | -2.202 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 9 | 9 | -1.1485 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 9 | -0.8656 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | -0.8382 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -0.8792 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.5528 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -1.5228 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 6 | 6 | -1.6163 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 4 | 4 | -2.0387 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -3.3174 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.4219 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.4229 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 1 | 1 | -0.435 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.435 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.435 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 1 | 1 | -0.435 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5099 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -3.4858 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 1 | 1 | 1.7646 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 1 | 1 | -1.4831 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 835 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 835 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 835 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 835 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 835 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 229, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 1577 | 1577 | None | -1.397 | 0.0406 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1527 | 1513 | None | -1.4835 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1465 | 1451 | None | -1.4116 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 647 | 647 | None | -1.5862 | 0.0278 | `hold_sample` |
| `ai_score_source` | `live` | 427 | 427 | None | -1.4446 | 0.0656 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 268 | 268 | None | -0.9313 | 0.041 | `hold_sample` |
| `ai_score_source` | `holding_ai_not_called` | 133 | 133 | None | -1.1739 | 0.0376 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 93 | 92 | None | -1.0853 | 0.0435 | `hold_sample` |
| `qty_reason` | `qty_none` | 92 | 92 | None | -1.0853 | 0.0435 | `hold_sample` |
| `time_bucket` | `time_unknown` | 93 | 92 | None | -1.0853 | 0.0435 | `hold_sample` |
| `ai_score_source` | `prior_valid` | 89 | 89 | None | -1.5259 | 0.045 | `hold_sample` |
| `arm` | `PYRAMID` | 66 | 66 | None | 0.6675 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 66 | 66 | None | 0.6675 | 1.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 62 | 62 | None | -3.1663 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 57 | 57 | None | -1.5398 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 53 | 52 | None | -1.1919 | 0.0769 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 51 | 51 | None | -1.2527 | 0.0196 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.33)` | 48 | 48 | None | -0.33 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 46 | 46 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 43 | 43 | None | 0.5072 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 1 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `stage` | `exit` | 1 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 1 | 1 | -0.435 | -0.58 | 0.0 | `hold_sample` |
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
