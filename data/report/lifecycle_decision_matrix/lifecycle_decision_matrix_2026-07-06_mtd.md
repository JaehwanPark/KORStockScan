# Lifecycle Decision Matrix - 2026-07-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-06_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `22116`
- source_rows_total: `37143`
- retained_rows: `22116`
- dropped_rows_by_source: `{}`
- joined_rows: `11429`
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
- lifecycle_flow_bucket_count: `163`
- lifecycle_flow_complete_count: `40`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0019`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1024 | 77 | 1.6139 | 0.1668 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 450 | 80 | -0.7327 | 0.3803 | `pass` | `NO_CHANGE` | False |
| `holding` | 298 | 80 | -1.1063 | 0.5976 | `pass` | `EXIT` | False |
| `scale_in` | 11038 | 10954 | -0.668 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 9306 | 238 | -0.9948 | 0.162 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 163, 'complete_flow_count': 40, 'incomplete_flow_count': 20721, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 9147 | 9077 | -0.9016 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1733 | 1719 | 0.583 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 145 | 145 | -1.0253 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 34 | 34 | 1.1486 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 10 | 10 | 6.3192 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 7 | 7 | 0.1786 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 6 | 6 | -1.1834 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.9659 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 10 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 8 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.6351 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.4958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 2 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dfd7c31acb` | 1 | 1 | -1.5916 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.8771 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 287, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 579 | 72 | 1.7809 | 2.4304 | 0.5417 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 507 | 57 | 0.8391 | 0.6212 | 0.4912 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 148 | 54 | 2.3286 | 3.83 | 0.6111 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 997 | 50 | 2.5018 | 4.1196 | 0.6 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 252 | 50 | 2.5018 | 4.1196 | 0.6 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 50 | 50 | 2.5018 | 4.1196 | 0.6 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 242 | 44 | 0.8639 | 1.2311 | 0.5227 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 122 | 41 | 2.7162 | 4.5249 | 0.6341 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 284 | 31 | 1.2723 | 1.5837 | 0.4839 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 544 | 27 | -0.0302 | -1.0559 | 0.4815 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 278 | 25 | 1.994 | 4.2262 | 0.64 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 485 | 25 | 0.22 | -0.7687 | 0.4 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 577 | 20 | 0.2301 | -1.4695 | 0.4 | `hold_sample` |
| `stale_bucket` | `fresh` | 192 | 16 | 0.4432 | -2.1863 | 0.3125 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | -0.6527 | 1.88 | 1.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 13 | 13 | 0.3462 | 0.3924 | 0.4615 | `hold_sample` |
| `score_band` | `score_66_69` | 26 | 11 | 5.3719 | 10.0399 | 0.8182 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 298 | 11 | 2.6673 | 3.7434 | 0.8182 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 10 | 10 | 0.7514 | -3.728 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 10 | 10 | 0.7178 | 1.0182 | 0.4 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 105, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 304 | 80 | -0.7327 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 288 | 80 | -0.7327 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 288 | 80 | -0.7327 | `keep_collecting` |
| `latency_state` | `simulated` | 288 | 80 | -0.7327 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 304 | 80 | -0.7327 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 288 | 80 | -0.7327 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 446 | 79 | -0.7421 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 258 | 69 | -0.8461 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 230 | 55 | -0.8783 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 179 | 46 | -0.2809 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 179 | 46 | -0.2809 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 175 | 45 | -0.2874 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 189 | 45 | -0.2874 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 175 | 45 | -0.2874 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 112 | 35 | -1.3054 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 113 | 35 | -1.3054 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 111 | 34 | -1.3441 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 109 | 34 | -1.3441 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 109 | 34 | -1.3441 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 75 | 26 | -1.3861 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 59 | 25 | -0.4126 | `keep_collecting` |
| `would_limit_fill` | `true` | 80 | 23 | -0.2671 | `keep_collecting` |
| `would_limit_fill` | `false` | 257 | 22 | -0.3085 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 55 | 22 | -1.5874 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 64 | 15 | -0.1689 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 78 | 13 | -0.5122 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 9 | -0.0143 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 26 | 8 | -0.2976 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 16 | 8 | -0.4513 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 31 | 5 | -0.2606 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 146 | 4 | -2.0866 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 4 | -0.2792 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 4 | 3 | 0.715 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 26 | 3 | -0.367 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -1.7491 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 288 | 80 | -1.1063 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 288 | 80 | -1.1063 | `hold_no_edge` |
| `holding_action` | `WAIT` | 264 | 70 | -1.2623 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 54 | 48 | -2.0788 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 44 | 44 | -2.096 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 15 | 15 | 0.6504 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 15 | 14 | 0.0138 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 12 | 12 | -0.072 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 12 | 12 | 0.4122 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 20 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `holding_action` | `BUY` | 4 | 1 | -1.5266 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.01 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 1 | -0.23 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.5514 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 208 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 194 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 55, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 163 | 163 | -0.978 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 163 | 163 | -0.978 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 163 | 163 | -0.978 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 162 | 162 | -1.4141 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 118 | 118 | -1.2069 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 65 | 65 | -1.0965 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 42 | 42 | -0.4977 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 40 | 40 | -0.514 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 28 | 28 | -2.0595 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 27 | 27 | -1.4611 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 27 | 27 | -0.7753 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | 0.3752 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 17 | 17 | 0.201 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.6926 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 12 | 12 | 0.5542 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 11 | 11 | -0.9903 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.5759 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 9078 | 10 | -0.6067 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.6067 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.6067 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 8 | 8 | -0.6924 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 6 | 6 | -1.0875 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 5 | 5 | -2.9426 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.9432 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.673 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.0225 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -2.9017 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.879 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.3261 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 2 | 2 | -2.678 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 1.5477 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.0039 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.0559 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 338, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 9787 | 9784 | None | -0.7465 | 0.1556 | `hold_sample` |
| `arm` | `AVG_DOWN` | 9297 | 9227 | None | -0.9928 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 9219 | 9149 | None | -0.9735 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3501 | 3501 | None | -0.7642 | 0.1765 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2706 | 2706 | None | -0.7035 | 0.1689 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1950 | 1949 | None | -0.8819 | 0.1047 | `hold_sample` |
| `arm` | `PYRAMID` | 1741 | 1727 | None | 0.5355 | 0.982 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1741 | 1727 | None | 0.5355 | 0.982 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1565 | 1565 | None | 0.4454 | 0.9802 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1512 | 1510 | None | -0.7085 | 0.147 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1283 | 1283 | None | -0.6799 | 0.1473 | `hold_sample` |
| `ai_score_source` | `live` | 924 | 924 | None | -0.7833 | 0.1504 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 392 | 392 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 360 | 360 | None | -0.54 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 229 | 229 | None | -0.9303 | 0.1048 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 185 | 185 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 173 | 173 | None | -0.811 | 0.052 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 171 | 171 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 166 | 166 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 143 | 143 | None | -1.06 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 20 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 10 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 20 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `stage` | `exit` | 10 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 20 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 10 | 10 | -0.6067 | -0.809 | 0.2 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 18 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.8587 | -1.145 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.0875 | -1.45 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.0875 | -1.45 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.0844 | -0.1125 | 0.5 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.3825 | -1.8433 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |

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
