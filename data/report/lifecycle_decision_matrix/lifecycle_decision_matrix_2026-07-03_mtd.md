# Lifecycle Decision Matrix - 2026-07-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-03_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `19062`
- source_rows_total: `32854`
- retained_rows: `19062`
- dropped_rows_by_source: `{}`
- joined_rows: `10265`
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
- lifecycle_flow_bucket_count: `142`
- lifecycle_flow_complete_count: `27`
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
| `entry` | 779 | 63 | 1.8053 | 0.1861 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 347 | 61 | -0.6628 | 0.3896 | `pass` | `NO_CHANGE` | False |
| `holding` | 224 | 61 | -1.0338 | 0.6317 | `pass` | `EXIT` | False |
| `scale_in` | 9967 | 9898 | -0.6716 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7745 | 182 | -0.9409 | 0.1501 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 142, 'complete_flow_count': 27, 'incomplete_flow_count': 18007, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8283 | 8226 | -0.9042 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1560 | 1548 | 0.5775 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 112 | 112 | -0.9952 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 27 | 27 | 1.4654 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 9 | 9 | 6.1809 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 6 | 6 | 0.3383 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -1.4367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 10 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 7 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.6351 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 2 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dfd7c31acb` | 1 | 1 | -1.5916 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.8771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5753169481` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b620fd9627` | 1 | 1 | -1.396 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 259, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 433 | 58 | 2.0291 | 2.931 | 0.5862 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 122 | 46 | 2.5804 | 4.271 | 0.6521 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 389 | 44 | 0.8311 | 0.6606 | 0.5227 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 758 | 42 | 2.8105 | 4.6578 | 0.6428 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 193 | 42 | 2.8105 | 4.6578 | 0.6428 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 42 | 42 | 2.8105 | 4.6578 | 0.6428 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 114 | 40 | 2.7887 | 4.6416 | 0.65 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 189 | 35 | 0.995 | 1.6808 | 0.5714 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 235 | 25 | 1.3073 | 1.6091 | 0.52 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 201 | 23 | 2.1145 | 4.5445 | 0.6522 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 416 | 21 | -0.205 | -1.1024 | 0.5238 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 355 | 17 | 0.3679 | -0.9051 | 0.4706 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 428 | 14 | 0.0793 | -1.7164 | 0.4286 | `hold_sample` |
| `stale_bucket` | `fresh` | 158 | 12 | 0.3944 | -2.7484 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 12 | 12 | 0.4247 | 0.4905 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 11 | 11 | -0.7544 | 1.7 | 1.0 | `source_quality_workorder` |
| `score_band` | `score_66_69` | 25 | 10 | 5.1527 | 9.8255 | 0.8 | `hold_sample` |
| `score_band` | `score_63_65` | 67 | 9 | 2.3528 | 3.1257 | 0.6667 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 220 | 9 | 3.2843 | 4.6629 | 0.8889 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 52 | 8 | 7.8473 | 13.7969 | 1.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 226 | 61 | -0.6628 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 215 | 61 | -0.6628 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 215 | 61 | -0.6628 | `keep_collecting` |
| `latency_state` | `simulated` | 215 | 61 | -0.6628 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 226 | 61 | -0.6628 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 215 | 61 | -0.6628 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 343 | 60 | -0.674 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 193 | 53 | -0.7899 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 170 | 41 | -0.8528 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 143 | 39 | -0.4156 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 143 | 39 | -0.4156 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 139 | 38 | -0.4269 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 149 | 38 | -0.4269 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 139 | 38 | -0.4269 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 76 | 23 | -1.0527 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 76 | 23 | -1.0527 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 73 | 22 | -1.101 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 72 | 22 | -1.101 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 72 | 22 | -1.101 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 45 | 20 | -0.2734 | `keep_collecting` |
| `would_limit_fill` | `true` | 62 | 20 | -0.3604 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 57 | 19 | -0.9917 | `keep_collecting` |
| `would_limit_fill` | `false` | 209 | 18 | -0.5007 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 44 | 16 | -1.2004 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 48 | 12 | -0.2998 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 63 | 11 | -0.8245 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 14 | 8 | -0.4513 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 14 | 7 | 0.0083 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 19 | 5 | -0.1426 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 3 | 3 | 0.715 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 119 | 3 | -1.7929 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 3 | 0.1214 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | -1.1397 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 13 | 1 | 0.01 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 4 | 1 | 0.01 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 215 | 61 | -1.0338 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 215 | 61 | -1.0338 | `hold_no_edge` |
| `holding_action` | `WAIT` | 199 | 54 | -1.1667 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 40 | 34 | -2.1505 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 31 | 31 | -2.2079 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 13 | 13 | 0.8962 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 13 | 12 | -0.1145 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 11 | 11 | -0.1072 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.6842 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 14 | 6 | 0.2445 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.5735 | `hold_sample` |
| `holding_action` | `BUY` | 2 | 1 | -1.5266 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.01 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.1943 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 154 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 145 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 126 | 126 | -0.9416 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 126 | 126 | -0.9416 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 126 | 126 | -0.9416 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 121 | 121 | -1.3786 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 90 | 90 | -1.1769 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 47 | 47 | -0.9938 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 32 | 32 | -0.5138 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 31 | 31 | -0.5248 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 23 | 23 | -0.9739 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 21 | 21 | -2.0258 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 21 | 21 | 0.3619 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 18 | 18 | -1.1363 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 15 | 15 | 0.1234 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -1.7621 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 10 | 10 | 0.8546 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 7572 | 9 | -0.655 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.655 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.655 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.8364 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 6 | 6 | -0.6434 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 6 | 6 | -1.0875 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 6 | 6 | -2.6134 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 4 | 4 | -2.9567 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.673 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.0225 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -2.9017 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.8408 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -1.977 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | 1.1582 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.0559 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_ai_momentum_decay|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 1 | 1 | 0.0559 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -3.1218 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 1 | 1 | 1.5441 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 305, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 9593 | 9592 | None | -0.7431 | 0.1577 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8400 | 8343 | None | -0.9871 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8330 | 8273 | None | -0.9678 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3501 | 3501 | None | -0.7642 | 0.1765 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2702 | 2702 | None | -0.7051 | 0.168 | `hold_sample` |
| `arm` | `PYRAMID` | 1567 | 1555 | None | 0.528 | 0.9813 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1567 | 1555 | None | 0.528 | 0.9813 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1438 | 1438 | None | 0.4484 | 0.9798 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1384 | 1384 | None | -0.8024 | 0.0917 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1277 | 1277 | None | -0.6803 | 0.1457 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1031 | 1030 | None | -0.8308 | 0.133 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 354 | 354 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 350 | 350 | None | -0.54 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 302 | 302 | None | -0.9531 | 0.0331 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 182 | 182 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 170 | 170 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 164 | 164 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 139 | 139 | None | -0.76 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 138 | 138 | None | -0.7762 | 0.058 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 135 | 135 | None | -1.06 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 29, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `stage` | `exit` | 9 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 18 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.655 | -0.8733 | 0.2222 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.9568 | -1.2757 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.0875 | -1.45 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.0875 | -1.45 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.0844 | -0.1125 | 0.5 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 3 | -1.3825 | -1.8433 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 1 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |

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
