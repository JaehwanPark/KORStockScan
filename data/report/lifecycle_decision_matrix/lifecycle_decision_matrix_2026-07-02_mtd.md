# Lifecycle Decision Matrix - 2026-07-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-02_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13974`
- source_rows_total: `23866`
- retained_rows: `13974`
- dropped_rows_by_source: `{}`
- joined_rows: `7104`
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
- lifecycle_flow_bucket_count: `117`
- lifecycle_flow_complete_count: `20`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0015`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 573 | 43 | 1.6752 | 0.1823 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 259 | 39 | -0.7092 | 0.2992 | `pass` | `NO_CHANGE` | False |
| `holding` | 172 | 39 | -0.8652 | 0.463 | `pass` | `EXIT` | False |
| `scale_in` | 6899 | 6850 | -0.6355 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6071 | 133 | -0.9298 | 0.1525 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 117, 'complete_flow_count': 20, 'incomplete_flow_count': 13186, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 5711 | 5673 | -0.8688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1096 | 1085 | 0.6011 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 85 | 85 | -1.0004 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 20 | 20 | 1.6398 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 6 | 6 | 0.3383 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 5 | 5 | 5.9457 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 3 | 3 | 3.8296 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -1.4367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 6 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -2.1328 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 1 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b620fd9627` | 1 | 1 | -1.396 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 1 | 1 | -1.654 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e8b25163c1` | 1 | 1 | 0.4047 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:c8b94ea5f8` | 1 | 1 | -1.9776 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:a2fde9fa15` | 1 | 1 | -1.4308 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b485054732` | 1 | 1 | -1.125 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 226, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 308 | 38 | 1.9997 | 3.0591 | 0.5263 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 90 | 32 | 2.3334 | 3.9955 | 0.5625 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 558 | 28 | 2.6433 | 4.5363 | 0.5357 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 147 | 28 | 2.6433 | 4.5363 | 0.5357 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 73 | 28 | 2.6671 | 4.4352 | 0.5714 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 28 | 28 | 2.6433 | 4.5363 | 0.5357 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 260 | 27 | 0.5714 | 0.2907 | 0.4074 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 148 | 27 | 1.0501 | 1.8434 | 0.4815 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 157 | 21 | 2.3188 | 5.0926 | 0.6667 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 306 | 15 | -0.132 | -0.5527 | 0.6 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 178 | 14 | 0.5784 | 0.4106 | 0.4286 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.7878 | 1.7911 | 1.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 9 | 9 | 0.5167 | 0.6444 | 0.4444 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 254 | 9 | 0.1582 | -0.851 | 0.4444 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 303 | 8 | 0.4296 | -1.1462 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 7 | 7 | 0.7466 | 1.1988 | 0.2857 | `hold_sample` |
| `stale_bucket` | `fresh` | 107 | 6 | 1.1765 | -3.02 | 0.1667 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 45 | 6 | 6.7662 | 11.9376 | 1.0 | `hold_sample` |
| `score_band` | `score_66_69` | 17 | 6 | 4.2712 | 9.1201 | 0.8333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 146 | 5 | -0.7912 | 0.496 | 0.8 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 100, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 175 | 39 | -0.7092 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 256 | 39 | -0.7092 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 167 | 39 | -0.7092 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 167 | 39 | -0.7092 | `keep_collecting` |
| `latency_state` | `simulated` | 167 | 39 | -0.7092 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 175 | 39 | -0.7092 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 167 | 39 | -0.7092 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 147 | 32 | -0.9985 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 113 | 26 | -0.2575 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 110 | 26 | -0.2575 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 117 | 26 | -0.2575 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 110 | 26 | -0.2575 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 113 | 26 | -0.2575 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 131 | 23 | -1.163 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 36 | 16 | -0.0568 | `keep_collecting` |
| `would_limit_fill` | `true` | 50 | 15 | -0.1754 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 55 | 13 | -1.6126 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 57 | 13 | -1.6126 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 54 | 13 | -1.6126 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 54 | 13 | -1.6126 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 57 | 13 | -1.6126 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 43 | 12 | -1.4477 | `keep_collecting` |
| `would_limit_fill` | `false` | 152 | 11 | -0.3694 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 10 | -1.9121 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 37 | 8 | -0.0806 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 13 | 7 | -0.2838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 11 | 6 | 0.4865 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 49 | 5 | -1.3966 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 17 | 4 | 0.5372 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 3 | 3 | 0.715 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 8 | 2 | 0.8746 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 81 | 1 | -3.5919 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -3.5919 | `source_quality_workorder` |
| `latency_state` | `caution` | 64 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 64 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 27, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 167 | 39 | -0.8652 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 167 | 39 | -0.8652 | `hold_no_edge` |
| `holding_action` | `WAIT` | 153 | 32 | -1.0526 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 26 | 21 | -1.9761 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 18 | 18 | -2.0457 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 10 | 10 | 1.0054 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | -0.2876 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | -0.3009 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.7493 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 12 | 6 | 0.2445 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.5735 | `hold_sample` |
| `holding_action` | `BUY` | 2 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.1943 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 128 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 121 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 95 | 95 | -0.9321 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 95 | 95 | -0.9321 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 95 | 95 | -0.9321 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 90 | 90 | -1.3523 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 68 | 68 | -1.1823 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 33 | 33 | -0.8956 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 22 | 22 | -0.5318 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 22 | 22 | -0.5318 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 17 | 17 | -0.6892 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 16 | 16 | 0.387 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | -1.9892 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 12 | 12 | -1.2491 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 11 | 0.1082 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 9 | 9 | -1.6958 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 7 | 7 | 0.9927 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 5943 | 5 | -1.1115 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.1115 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.1115 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 5 | 5 | -1.1115 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 5 | 5 | -0.9661 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | -0.7126 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.6523 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.673 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 3 | 3 | -2.6329 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 0.03 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.3885 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 2 | 2 | -0.5465 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.8157 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -3.1218 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.9776 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 1 | 1 | 0.8991 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.35 | `hold_sample` |
| `exit_rule` | `exit_rule_unknown` | 5938 | 0 | None | `source_quality_workorder` |
| `profit_band` | `profit_unknown` | 5938 | 0 | None | `source_quality_workorder` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 149 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 5789 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 265, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 6847 | 6847 | None | -0.7147 | 0.1553 | `hold_sample` |
| `arm` | `AVG_DOWN` | 5797 | 5759 | None | -0.9524 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 5752 | 5714 | None | -0.9344 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 2405 | 2405 | None | -0.7607 | 0.1792 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 1889 | 1889 | None | -0.6643 | 0.1435 | `hold_sample` |
| `arm` | `PYRAMID` | 1102 | 1091 | None | 0.5438 | 0.977 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1102 | 1091 | None | 0.5438 | 0.977 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1008 | 1008 | None | 0.4579 | 0.9752 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 981 | 981 | None | -0.6435 | 0.1417 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 931 | 931 | None | -0.7636 | 0.1031 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 641 | 641 | None | -0.7284 | 0.1966 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 348 | 348 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 238 | 238 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 178 | 178 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 160 | 160 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 139 | 139 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 106 | 106 | None | -0.756 | 0.0755 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.33)` | 102 | 102 | None | -0.33 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 90 | 90 | None | -0.08 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.62)` | 90 | 90 | None | -0.62 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 5 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `stage` | `exit` | 5 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 10 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 5 | 5 | -1.1115 | -1.482 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.3825 | -1.8433 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 5 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 5 | 0 | None | None | None | `hold_sample` |

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
