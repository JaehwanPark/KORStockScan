# Lifecycle Decision Matrix - 2026-07-07

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-07_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `26179`
- source_rows_total: `42677`
- retained_rows: `26179`
- dropped_rows_by_source: `{}`
- joined_rows: `12788`
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
- lifecycle_flow_bucket_count: `186`
- lifecycle_flow_complete_count: `54`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0022`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1314 | 88 | 1.3185 | 0.1512 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 535 | 103 | -0.7002 | 0.4344 | `pass` | `NO_CHANGE` | False |
| `holding` | 352 | 103 | -1.1589 | 0.6829 | `pass` | `EXIT` | False |
| `scale_in` | 12316 | 12207 | -0.6917 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 11662 | 287 | -0.9907 | 0.1518 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 186, 'complete_flow_count': 54, 'incomplete_flow_count': 24430, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 10285 | 10198 | -0.9255 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1849 | 1827 | 0.6274 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 163 | 163 | -1.0186 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 37 | 37 | 1.0636 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 12 | 12 | 4.8647 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 9 | 9 | 0.5362 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -0.9756 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 4 | 4 | -1.7356 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -1.3367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.8433 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 11 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 13 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 2 | 2 | -1.8977 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.6351 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.4958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:50ebb4b990` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 308, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 795 | 82 | 1.4623 | 1.9646 | 0.5122 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 703 | 65 | 0.6917 | 0.2952 | 0.4615 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 170 | 60 | 2.0218 | 3.3667 | 0.6 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1281 | 55 | 2.1923 | 3.6389 | 0.5818 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 279 | 55 | 2.1923 | 3.6389 | 0.5818 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 55 | 55 | 2.1923 | 3.6389 | 0.5818 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 256 | 48 | 0.7998 | 1.1505 | 0.5417 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 142 | 43 | 2.5426 | 4.2503 | 0.6279 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 397 | 38 | 0.7779 | 0.8063 | 0.4211 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 734 | 33 | -0.1377 | -1.077 | 0.4545 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 673 | 28 | 0.1581 | -0.7309 | 0.3929 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 805 | 25 | 0.0318 | -1.4976 | 0.36 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 338 | 25 | 1.994 | 4.2262 | 0.64 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 243 | 18 | 0.2421 | -2.3211 | 0.2778 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.6767 | 2.0687 | 1.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 15 | 15 | 0.1653 | 0.172 | 0.4667 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | 0.3893 | -3.6357 | 0.0 | `hold_sample` |
| `score_band` | `score_66_69` | 29 | 13 | 4.175 | 8.0434 | 0.6923 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 392 | 13 | 2.4415 | 3.4425 | 0.8462 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 146 | 12 | 0.5187 | -0.015 | 0.4167 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 113, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 358 | 103 | -0.7002 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 338 | 103 | -0.7002 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 338 | 103 | -0.7002 | `keep_collecting` |
| `latency_state` | `simulated` | 338 | 103 | -0.7002 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 358 | 103 | -0.7002 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 338 | 103 | -0.7002 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 531 | 102 | -0.7071 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 308 | 92 | -0.7813 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 273 | 72 | -0.8759 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 214 | 58 | -0.273 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 214 | 58 | -0.273 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 210 | 57 | -0.2779 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 228 | 57 | -0.2779 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 210 | 57 | -0.2779 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 127 | 46 | -1.2234 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 128 | 46 | -1.2234 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 126 | 45 | -1.2508 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 124 | 45 | -1.2508 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 124 | 45 | -1.2508 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 66 | 31 | -0.292 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 88 | 31 | -1.4021 | `keep_collecting` |
| `would_limit_fill` | `true` | 101 | 31 | -0.3104 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 63 | 27 | -1.5684 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 306 | 26 | -0.2392 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 81 | 20 | -0.3309 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 91 | 16 | -0.2717 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 20 | 11 | -0.2732 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 38 | 10 | -0.6648 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 10 | -0.1872 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 26 | 8 | -0.2976 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 31 | 7 | -0.9524 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 171 | 5 | -1.233 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -0.7665 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 18 | 4 | -0.2792 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 4 | 3 | 0.715 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 338 | 103 | -1.1589 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 338 | 103 | -1.1589 | `hold_no_edge` |
| `holding_action` | `WAIT` | 312 | 92 | -1.2913 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 71 | 63 | -2.1215 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 59 | 59 | -2.1372 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 18 | 17 | -0.0027 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 16 | 16 | 0.6743 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 14 | 14 | -0.0483 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 13 | 13 | 0.46 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 20 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 7 | 3 | -0.2767 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 1.4547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.4063 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 14 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 235 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 220 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 57, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 194 | 194 | -1.4503 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 190 | 190 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 190 | 190 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 190 | 190 | -0.9428 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 136 | 136 | -1.2032 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 83 | 83 | -1.1687 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 51 | 51 | -0.4889 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 47 | 47 | -0.5136 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 37 | 37 | -1.5692 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 37 | 37 | -2.0025 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 31 | 31 | 0.4189 | `candidate_recovery_or_relax` |
| `exit_outcome` | `MISSED_UPSIDE` | 30 | 30 | -0.8281 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 20 | 20 | 0.1589 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 16 | 16 | -0.8814 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 16 | 16 | -1.611 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 15 | 15 | -2.5277 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 11389 | 14 | -0.5866 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.5866 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.5866 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 13 | 13 | 0.591 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.6304 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 8 | 8 | -3.4526 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -1.0275 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.734 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 5 | 5 | 2.1148 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.1269 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -2.6338 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.9432 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.673 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.1667 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.4522 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 2 | 2 | -2.678 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.0039 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 378, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 10457 | 10370 | None | -1.0253 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 10357 | 10270 | None | -1.0036 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 9884 | 9873 | None | -0.7478 | 0.1545 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3503 | 3503 | None | -0.7645 | 0.1764 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3149 | 3141 | None | -0.9678 | 0.0927 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2713 | 2713 | None | -0.7056 | 0.1692 | `hold_sample` |
| `arm` | `PYRAMID` | 1859 | 1837 | None | 0.5823 | 0.9831 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1859 | 1837 | None | 0.5823 | 0.9831 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1594 | 1594 | None | 0.4464 | 0.9805 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1556 | 1553 | None | -0.6787 | 0.1558 | `hold_sample` |
| `ai_score_source` | `live` | 1491 | 1491 | None | -0.9479 | 0.1241 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1292 | 1292 | None | -0.6813 | 0.1471 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 813 | 813 | None | -0.9346 | 0.0972 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 421 | 421 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 370 | 370 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 197 | 197 | None | -0.7933 | 0.0558 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 192 | 192 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 183 | 183 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 174 | 174 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 144 | 144 | None | -0.76 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 28 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 14 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 28 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `stage` | `exit` | 14 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 28 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 14 | 14 | -0.5866 | -0.7821 | 0.1429 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 26 | 13 | -0.6185 | -0.8246 | 0.1538 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 24 | 12 | -0.7513 | -1.0017 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -1.0275 | -1.37 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -1.0275 | -1.37 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 6 | -0.3388 | -0.4517 | 0.3333 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.9195 | -1.226 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | -0.265 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1987 | -0.265 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
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
