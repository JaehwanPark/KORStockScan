# Lifecycle Decision Matrix - 2026-09-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-02_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4600`
- source_rows_total: `6541`
- retained_rows: `4600`
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
- lifecycle_flow_bucket_count: `53`
- lifecycle_flow_complete_count: `21`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.006`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1231 | 6 | 0.1395 | 0.0015 | `pass` | `NO_CHANGE` | False |
| `submit` | 127 | 21 | -1.0471 | 0.174 | `pass` | `NO_CHANGE` | False |
| `holding` | 26 | 21 | -0.9952 | 0.8495 | `pass` | `EXIT` | False |
| `scale_in` | 2288 | 2286 | -0.9141 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 928 | 48 | -0.9973 | 0.1393 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 53, 'complete_flow_count': 21, 'incomplete_flow_count': 3477, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2023 | 2021 | -1.1087 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 265 | 265 | 0.5697 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 3 | 3 | -1.08 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 1 | 1 | -0.46 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -3.5005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 1 | 1 | -0.78 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -0.49 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 1 | 1 | -0.77 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:04a7285e92` | 1 | 1 | -0.95 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:520515b37c` | 1 | 1 | -1.03 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.74 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c876ed88d1` | 1 | 1 | -0.94 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e426f49f2` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 178, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 498 | 4 | 0.3656 | -0.64 | 0.5 | `hold_sample` |
| `stale_bucket` | `fresh` | 572 | 4 | 0.3656 | -0.64 | 0.5 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 426 | 4 | 0.3656 | -0.64 | 0.5 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1022 | 4 | 0.3656 | -0.64 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | 0.3316 | 0.36 | 1.0 | `hold_sample` |
| `score_band` | `score_70p` | 70 | 3 | 0.0889 | -0.3233 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 338 | 3 | -0.1595 | -0.8767 | 0.3333 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 432 | 3 | 0.2038 | -1.0167 | 0.3333 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 70 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 766 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 107 | 2 | 0.3716 | -0.63 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 704 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 245 | 2 | 0.3596 | -0.65 | 0.5 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 71 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.0131 | -1.48 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 9 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `score_band` | `score_63_65` | 15 | 2 | 0.2119 | -0.59 | 0.5 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 502 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 212 | 2 | 0.7238 | 0.375 | 1.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 592 | 1 | 0.851 | 0.49 | 1.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 86, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 121 | 21 | -1.0471 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 127 | 21 | -1.0471 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 23 | 21 | -1.0471 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 23 | 21 | -1.0471 | `keep_collecting` |
| `latency_state` | `simulated` | 23 | 21 | -1.0471 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 121 | 21 | -1.0471 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 23 | 21 | -1.0471 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 19 | 17 | -1.5904 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 16 | 16 | -1.4549 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 16 | 16 | -1.4549 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 16 | 16 | -1.4549 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 16 | 16 | -1.4549 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 16 | 16 | -1.4549 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 17 | 15 | -1.3961 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 19 | 14 | -2.0324 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -2.3051 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 7 | 5 | 0.2579 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 7 | 5 | 0.2579 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 105 | 5 | 0.2579 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 7 | 5 | 0.2579 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 7 | 5 | 0.2579 | `keep_collecting` |
| `would_limit_fill` | `false` | 110 | 4 | 0.2858 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 4 | 1.2618 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 3 | 0.0196 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 3 | 3 | -0.3694 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 3 | 0.0973 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 2 | 2 | 2.5871 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -0.3961 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 0.851 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.1467 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1855 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 1 | 1 | 0.1467 | `keep_collecting` |
| `latency_state` | `caution` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 3 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 23 | 21 | -0.9952 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 23 | 21 | -0.9952 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 19 | 17 | -1.5527 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 14 | 11 | -1.9875 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.9875 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | -0.0761 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 4 | 4 | 1.3739 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.3914 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.2391 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 34 | 34 | -1.4069 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 23 | 23 | -0.9592 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 22 | 22 | -0.989 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 22 | 22 | -0.989 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 22 | 22 | -0.989 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 19 | 19 | -1.0716 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 12 | 12 | 0.1398 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 10 | 10 | -1.5371 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 7 | 7 | -1.1281 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.0084 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | 0.2009 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -1.3522 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 6 | 6 | -3.0279 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.3801 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.7925 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -1.35 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -1.35 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 3 | 3 | -1.35 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 3 | 3 | -0.4667 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | 0.1583 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.7548 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7548 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.7961 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.6672 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -4.527 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -2.4707 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 880 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 880 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 880 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 221, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2288 | 2286 | None | -1.0117 | 0.1133 | `hold_sample` |
| `qty_reason` | `qty_none` | 2286 | 2286 | None | -1.0117 | 0.1133 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2286 | 2286 | None | -1.0117 | 0.1133 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2288 | 2286 | None | -1.0117 | 0.1133 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2023 | 2021 | None | -1.2167 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2001 | 1999 | None | -1.1937 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1444 | 1444 | None | -1.0223 | 0.1392 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1408 | 1408 | None | -1.5723 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1297 | 1297 | None | -1.1215 | 0.1588 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1260 | 1258 | None | -0.8475 | 0.2059 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1030 | 1028 | None | -1.2126 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 615 | 615 | None | -1.3756 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 569 | 569 | None | -0.4257 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 557 | 557 | None | -0.5573 | 0.3106 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 544 | 544 | None | -1.0314 | 0.011 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 532 | 532 | None | -1.2867 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 387 | 387 | None | -1.0891 | 0.062 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 280 | 280 | None | -0.6267 | 0.1464 | `hold_sample` |
| `arm` | `PYRAMID` | 265 | 265 | None | 0.5514 | 0.9774 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 265 | 265 | None | 0.5514 | 0.9774 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `stage` | `exit` | 3 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -1.35 | -1.8 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 3 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | None | None | `hold_sample` |

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
