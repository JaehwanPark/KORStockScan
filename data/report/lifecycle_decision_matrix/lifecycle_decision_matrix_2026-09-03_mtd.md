# Lifecycle Decision Matrix - 2026-09-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-09-03_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7522`
- source_rows_total: `10435`
- retained_rows: `7522`
- dropped_rows_by_source: `{}`
- joined_rows: `4011`
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
- lifecycle_flow_bucket_count: `68`
- lifecycle_flow_complete_count: `33`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1853 | 15 | 0.0188 | 0.0084 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 203 | 35 | -0.7356 | 0.2075 | `pass` | `NO_CHANGE` | False |
| `holding` | 41 | 35 | -1.0483 | 0.9097 | `pass` | `EXIT` | False |
| `scale_in` | 3871 | 3858 | -0.8709 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1554 | 68 | -1.0026 | 0.1171 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 68, 'complete_flow_count': 33, 'incomplete_flow_count': 5837, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3512 | 3500 | -1.0189 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 359 | 358 | 0.575 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5ee2a7cfd7` | 4 | 4 | -1.1925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:42bc391d5b` | 2 | 2 | -0.7738 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:a6af469504` | 2 | 2 | -0.56 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0cb91a7ba6` | 2 | 2 | -0.68 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:36904223da` | 2 | 2 | -0.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7a29eed6f7` | 1 | 1 | -1.0614 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f4d0891804` | 1 | 1 | -0.88 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:44fb83e208` | 1 | 1 | -0.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:4bb9b08477` | 1 | 1 | -0.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:441959da5f` | 1 | 1 | -1.677 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e95b96a4e9` | 1 | 1 | -1.38 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0bc92a886` | 1 | 1 | -0.98 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e6cc63e69d` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:e629891351` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 1 | 1 | -3.5005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:691e82f073` | 1 | 1 | -0.5956 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b31cc048c8` | 1 | 1 | -0.49 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:8de6b2fa46` | 1 | 1 | -0.77 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 221, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 824 | 13 | 0.0698 | -1.4985 | 0.1538 | `hold_sample` |
| `stale_bucket` | `fresh` | 899 | 13 | 0.0698 | -1.4985 | 0.1538 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 706 | 13 | 0.0698 | -1.4985 | 0.1538 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1520 | 13 | 0.0698 | -1.4985 | 0.1538 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 217 | 9 | 0.0034 | -1.2966 | 0.1111 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 9 | 9 | -0.0821 | -1.4855 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 40 | 9 | -0.0321 | -1.2877 | 0.1111 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 715 | 9 | 0.0441 | -1.3367 | 0.1111 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 503 | 8 | -0.1898 | -1.4537 | 0.125 | `hold_sample` |
| `score_band` | `score_70p` | 115 | 5 | 0.0847 | -1.496 | 0.4 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 407 | 4 | 0.219 | -1.9525 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 4 | 4 | -0.2469 | -1.4375 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 504 | 4 | -0.0381 | -2.0225 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | 0.3316 | 0.36 | 1.0 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 179 | 3 | -0.1139 | -2.6467 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 326 | 3 | 0.6506 | -0.29 | 0.6667 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 98 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1084 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 982 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 99 | 2 | -0.3126 | -0.555 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 99, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 194 | 35 | -0.7356 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 199 | 35 | -0.7356 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 37 | 35 | -0.7356 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 37 | 35 | -0.7356 | `keep_collecting` |
| `latency_state` | `simulated` | 37 | 35 | -0.7356 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 194 | 35 | -0.7356 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 37 | 35 | -0.7356 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 29 | 27 | -1.1142 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 28 | 26 | -0.9398 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 20 | 19 | -1.2652 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 19 | 19 | -1.2652 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 19 | 19 | -1.2652 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 19 | 19 | -1.2652 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 19 | 19 | -1.2652 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 18 | 16 | -0.1065 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 18 | 16 | -0.1065 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 170 | 16 | -0.1065 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 18 | 16 | -0.1065 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 18 | 16 | -0.1065 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 24 | 15 | -1.9293 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -2.3051 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 178 | 10 | 0.1135 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 8 | 8 | 0.5424 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 10 | 8 | 0.042 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 6 | 6 | -0.4733 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 5 | 5 | -0.3293 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 4 | 4 | 0.0844 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 7 | 4 | 1.225 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 4 | 4 | -0.6675 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0296 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.4262 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 2 | 0.3994 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | -0.0849 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.9886 | `source_quality_workorder` |
| `latency_state` | `caution` | 6 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 24, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 37 | 35 | -1.0483 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 37 | 35 | -1.0483 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 31 | 29 | -1.3969 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 28 | 24 | -1.5689 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 23 | 23 | -1.5642 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.0655 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 6 | 6 | 0.6362 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.1789 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | -0.3914 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | -1.35 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.677 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.7784 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 49 | 49 | -1.3436 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 36 | 36 | -0.974 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 28 | 28 | -0.9632 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 28 | 28 | -0.9632 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 28 | 28 | -0.9632 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 21 | 21 | -1.1081 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 16 | 16 | -1.4133 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | 0.129 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 12 | 12 | -1.0181 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.78 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | -2.4877 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 8 | 8 | -0.0292 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 8 | -0.0075 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 8 | 8 | -0.4776 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 7 | 7 | -1.4579 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.5286 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -0.7162 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.5838 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -1.5356 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.5356 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 4 | 4 | 0.1183 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -0.9692 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.6854 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.0019 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | 0.5293 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 2 | 2 | -0.7961 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.5956 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -2.6672 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.4217 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.9741 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg070_neg010` | 1 | 1 | -0.1205 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.8886 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | 0.3171 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.7784 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | -1.35 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 1486 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 280, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 3870 | 3858 | None | -0.9606 | 0.0913 | `hold_sample` |
| `qty_reason` | `qty_none` | 3859 | 3858 | None | -0.9606 | 0.0913 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3871 | 3858 | None | -0.9606 | 0.0913 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3857 | 3856 | None | -0.9615 | 0.0908 | `hold_sample` |
| `arm` | `AVG_DOWN` | 3512 | 3500 | None | -1.1155 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3480 | 3468 | None | -1.096 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2483 | 2483 | None | -0.9829 | 0.1043 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2324 | 2324 | None | -1.4575 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2177 | 2177 | None | -1.0609 | 0.1213 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2066 | 2053 | None | -0.8308 | 0.1714 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1818 | 1805 | None | -1.1082 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1103 | 1103 | None | -0.4648 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1095 | 1095 | None | -1.1675 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 960 | 960 | None | -1.1649 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 956 | 956 | None | -0.9351 | 0.0282 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 827 | 827 | None | -0.6743 | 0.2672 | `hold_sample` |
| `ai_score_source` | `live` | 631 | 631 | None | -0.9666 | 0.0808 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 467 | 467 | None | -0.6507 | 0.1156 | `hold_sample` |
| `arm` | `PYRAMID` | 359 | 358 | None | 0.5539 | 0.9833 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 359 | 358 | None | 0.5539 | 0.9833 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -1.5356 | -2.0475 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |

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
