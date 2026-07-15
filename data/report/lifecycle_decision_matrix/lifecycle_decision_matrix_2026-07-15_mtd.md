# Lifecycle Decision Matrix - 2026-07-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-15_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `33805`
- source_rows_total: `54207`
- retained_rows: `33805`
- dropped_rows_by_source: `{}`
- joined_rows: `16213`
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
- lifecycle_flow_bucket_count: `283`
- lifecycle_flow_complete_count: `115`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0037`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2564 | 126 | 0.8464 | 0.1243 | `pass` | `NO_CHANGE` | False |
| `submit` | 843 | 163 | -0.6294 | 0.4816 | `pass` | `NO_CHANGE` | False |
| `holding` | 532 | 163 | -1.2077 | 0.7051 | `pass` | `EXIT` | False |
| `scale_in` | 15537 | 15345 | -0.7328 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14329 | 416 | -1.0279 | 0.2146 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 283, 'complete_flow_count': 115, 'incomplete_flow_count': 30679, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 13080 | 12923 | -0.9615 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2227 | 2192 | 0.6315 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 200 | 200 | -1.0198 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 43 | 43 | 0.8851 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 13 | 13 | 4.4797 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 13 | 13 | 0.2535 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.9509 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.308 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.82 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 3 | 3 | -1.2733 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 3 | 3 | -1.06 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 2 | 2 | -1.6292 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 16 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 379, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1461 | 113 | 1.0456 | 1.0446 | 0.4602 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1353 | 91 | 0.491 | -0.1388 | 0.4286 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 486 | 68 | 1.7165 | 2.9084 | 0.5882 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1612 | 64 | -0.1951 | -1.3622 | 0.4062 | `source_quality_workorder` |
| `exit_rule` | `exit_unknown` | 2500 | 62 | 1.9216 | 3.1863 | 0.5645 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 365 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 62 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 427 | 60 | 0.5128 | 0.6727 | 0.5333 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 771 | 50 | 0.6097 | 0.499 | 0.44 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1614 | 49 | 0.0098 | -1.59 | 0.3265 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1181 | 48 | 0.1906 | -1.3268 | 0.2917 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 252 | 47 | 2.3042 | 3.8975 | 0.6383 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 604 | 34 | 1.1818 | 2.2848 | 0.5294 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 30 | 30 | 0.1204 | -3.5867 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 919 | 29 | 0.0025 | -1.3772 | 0.3103 | `hold_sample` |
| `stale_bucket` | `fresh` | 529 | 28 | 0.0294 | -2.2382 | 0.25 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 668 | 26 | -0.2631 | -0.4464 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 26 | 26 | -0.5044 | 1.9508 | 1.0 | `source_quality_workorder` |
| `stale_bucket` | `stale_high` | 969 | 25 | -0.2964 | -0.9164 | 0.44 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 461 | 25 | 0.3393 | -1.0974 | 0.36 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 131, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 606 | 163 | -0.6294 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 509 | 163 | -0.6294 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 509 | 163 | -0.6294 | `keep_collecting` |
| `latency_state` | `simulated` | 509 | 163 | -0.6294 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 606 | 163 | -0.6294 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 826 | 162 | -0.6333 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 506 | 160 | -0.5682 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 472 | 148 | -0.6879 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 428 | 122 | -0.5824 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 319 | 93 | -0.278 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 319 | 93 | -0.278 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 314 | 92 | -0.2811 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 407 | 92 | -0.2811 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 314 | 92 | -0.2811 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 193 | 71 | -1.0807 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 195 | 71 | -1.0807 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 192 | 70 | -1.0962 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 190 | 70 | -1.0962 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 190 | 70 | -1.0962 | `keep_collecting` |
| `would_limit_fill` | `false` | 500 | 46 | -0.2085 | `keep_collecting` |
| `would_limit_fill` | `true` | 148 | 46 | -0.3538 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 131 | 44 | -1.2155 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 79 | 38 | -0.5228 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 84 | 37 | -1.1877 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 147 | 35 | -0.1834 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 122 | 31 | -0.1763 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 81 | 22 | -0.7762 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 67 | 17 | -0.7135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 26 | 15 | -0.7205 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 32 | 11 | -0.3106 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 19 | 11 | -0.2884 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 213 | 5 | -1.233 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 21 | 5 | -0.0276 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 5 | 4 | 0.6577 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -0.7665 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 509 | 163 | -1.2077 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 509 | 163 | -1.2077 | `hold_no_edge` |
| `holding_action` | `WAIT` | 480 | 151 | -1.3029 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 114 | 103 | -2.1108 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 99 | 99 | -2.1197 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 23 | 21 | 0.0351 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 21 | 21 | 0.5767 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 18 | 18 | 0.006 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 18 | 18 | 0.4057 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 21 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 12 | 9 | -0.1744 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | -0.2532 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 23 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 346 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 23 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 329 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 67, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 281 | 281 | -1.5075 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 257 | 257 | -0.9542 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 257 | 257 | -0.9542 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 257 | 257 | -0.9542 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 183 | 183 | -1.2196 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 136 | 136 | -1.2633 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 70 | 70 | -0.5046 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 68 | 68 | -1.9738 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 64 | 64 | -0.5341 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 56 | 56 | -1.6345 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 54 | 54 | -0.8909 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 46 | 46 | 0.4514 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 29 | 29 | -2.4349 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 27 | 27 | -1.5318 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 26 | 26 | -1.2369 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 24 | 24 | 0.1518 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 13062 | 23 | -0.4595 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.4595 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.4595 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 18 | 18 | 0.5003 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 14 | 14 | -0.057 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 12 | 12 | -1.8538 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | -3.8938 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 11 | 11 | -1.0323 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 11 | 11 | -0.5774 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 2.1642 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.3769 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -1.0317 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.19 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -3.4922 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 0.554 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.166 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.3504 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -3.6004 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.3481 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 462, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 13296 | 13139 | None | -1.08 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 13152 | 12995 | None | -1.056 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10319 | 10297 | None | -0.7569 | 0.1526 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 6036 | 6018 | None | -1.0374 | 0.0889 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3510 | 3509 | None | -0.764 | 0.177 | `hold_sample` |
| `ai_score_source` | `live` | 3289 | 3289 | None | -1.0626 | 0.1149 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2744 | 2744 | None | -0.7044 | 0.1735 | `hold_sample` |
| `arm` | `PYRAMID` | 2241 | 2206 | None | 0.59 | 0.9827 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2241 | 2206 | None | 0.59 | 0.9827 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1832 | 1832 | None | 0.4384 | 0.9809 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1741 | 1738 | None | -0.649 | 0.1867 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1666 | 1666 | None | -0.9411 | 0.1056 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1407 | 1407 | None | -1.1724 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1327 | 1327 | None | -0.6849 | 0.1522 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1355 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `qty_reason` | `qty_none` | 1317 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1357 | 1315 | None | -0.9189 | 0.0914 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 745 | 745 | None | -1.4605 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 681 | 681 | None | -1.0623 | 0.1101 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 33, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 46 | 23 | -0.4595 | -0.6126 | 0.2174 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 23 | 23 | -0.4595 | -0.6126 | 0.2174 | `hold_sample` |
| `stage` | `exit` | 23 | 23 | -0.4595 | -0.6126 | 0.2174 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 46 | 23 | -0.4595 | -0.6126 | 0.2174 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 23 | 23 | -0.4595 | -0.6126 | 0.2174 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 44 | 22 | -0.4282 | -0.5709 | 0.2273 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | -0.5025 | -0.67 | 0.25 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 36 | 18 | -0.6983 | -0.9311 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 13 | -0.251 | -0.3346 | 0.3846 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 11 | -1.0323 | -1.3764 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0207 | -1.361 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.1736 | -0.2314 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.1736 | -0.2314 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.925 | -1.2333 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |

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
