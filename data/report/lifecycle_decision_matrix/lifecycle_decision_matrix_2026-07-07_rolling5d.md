# Lifecycle Decision Matrix - 2026-07-07

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-07_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `12205`
- source_rows_total: `18811`
- retained_rows: `12205`
- dropped_rows_by_source: `{}`
- joined_rows: `5684`
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
- lifecycle_flow_bucket_count: `127`
- lifecycle_flow_complete_count: `34`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.003`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 741 | 45 | 0.9777 | 0.1214 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 276 | 64 | -0.6947 | 0.5168 | `pass` | `NO_CHANGE` | False |
| `holding` | 180 | 64 | -1.3379 | 0.8168 | `pass` | `EXIT` | False |
| `scale_in` | 5417 | 5357 | -0.7636 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5591 | 154 | -1.0434 | 0.1511 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 127, 'complete_flow_count': 34, 'incomplete_flow_count': 11244, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4574 | 4525 | -0.9965 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 753 | 742 | 0.6658 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 78 | 78 | -1.0383 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 17 | 17 | 0.3859 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 7 | 7 | 4.0925 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 6 | 6 | -0.745 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 3 | 3 | 3.785 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -1.3367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.8433 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 3 | 3 | 0.932 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 5 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.3384 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.4958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:50ebb4b990` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:05b5bc258b` | 1 | 1 | -0.37 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dfd7c31acb` | 1 | 1 | -1.5916 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.8771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5753169481` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:737c4560d0` | 1 | 1 | -2.2711 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 231, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 487 | 44 | 0.9982 | 1.0194 | 0.5 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 443 | 38 | 0.7773 | 0.2984 | 0.5 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 80 | 28 | 1.6657 | 2.648 | 0.6428 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 723 | 27 | 1.7245 | 2.7083 | 0.6296 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 132 | 27 | 1.7245 | 2.7083 | 0.6296 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 27 | 27 | 1.7245 | 2.7083 | 0.6296 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 219 | 24 | 0.8943 | 1.0371 | 0.4167 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 108 | 21 | 0.478 | 0.2596 | 0.619 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 419 | 19 | 0.1581 | -0.6741 | 0.3684 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 428 | 18 | -0.1425 | -1.5139 | 0.3333 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 502 | 17 | -0.1554 | -1.6629 | 0.2941 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 69 | 15 | 2.3103 | 3.9053 | 0.7333 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 136 | 12 | -0.2251 | -1.9717 | 0.3333 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 121 | 11 | 0.5762 | 0.0092 | 0.4545 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 251 | 10 | 1.8487 | 2.8488 | 0.9 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 9 | 9 | 0.1097 | -3.62 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 289 | 8 | -0.1579 | -1.2288 | 0.25 | `hold_sample` |
| `score_band` | `score_63_65` | 36 | 8 | 0.7526 | 0.2621 | 0.5 | `hold_sample` |
| `score_band` | `score_66_69` | 12 | 7 | 4.0925 | 7.1205 | 0.5714 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 90 | 7 | 0.4132 | -0.888 | 0.2857 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 102, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 183 | 64 | -0.6947 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 171 | 64 | -0.6947 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 171 | 64 | -0.6947 | `keep_collecting` |
| `latency_state` | `simulated` | 171 | 64 | -0.6947 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 183 | 64 | -0.6947 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 171 | 64 | -0.6947 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 275 | 63 | -0.7059 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 161 | 60 | -0.6655 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 142 | 49 | -0.7412 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 70 | 33 | -1.0701 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 71 | 33 | -1.0701 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 71 | 32 | -1.1038 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 101 | 32 | -0.2855 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 70 | 32 | -1.1038 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 70 | 32 | -1.1038 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 101 | 32 | -0.2855 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 100 | 31 | -0.2951 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 111 | 31 | -0.2951 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 100 | 31 | -0.2951 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 45 | 19 | -1.3732 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 29 | 17 | -1.3662 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 51 | 16 | -0.4369 | `keep_collecting` |
| `would_limit_fill` | `false` | 154 | 15 | -0.1437 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 30 | 15 | -0.5428 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 44 | 12 | -0.4977 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 42 | 11 | 0.2396 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 28 | 10 | -0.6648 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 7 | -0.9524 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 9 | 4 | -1.1323 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 90 | 4 | -0.6433 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 7 | 4 | -1.1977 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 7 | 4 | -0.2548 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | 0.1753 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 0.0045 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 10 | 2 | -1.4329 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 171 | 64 | -1.3379 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 171 | 64 | -1.3379 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 159 | 60 | -1.4186 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 45 | 42 | -2.1943 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 41 | 41 | -2.1774 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 10 | 9 | 0.2504 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | 0.2043 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | 0.1224 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | 0.1224 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 8 | 3 | -0.0281 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 7 | 3 | -0.2767 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 3 | 3 | 1.4547 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.4063 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 107 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 99 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 104 | 104 | -1.535 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 95 | 95 | -0.9534 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 95 | 95 | -0.9534 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 95 | 95 | -0.9534 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 68 | 68 | -1.2241 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 50 | 50 | -1.3489 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 29 | 29 | -0.4564 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 25 | 25 | -1.7228 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 25 | 25 | -0.4976 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 23 | 23 | -2.0107 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | 0.4529 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 13 | 13 | -1.0097 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 12 | 12 | -0.9376 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 11 | 11 | -2.4823 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 5446 | 9 | -0.295 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.221 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.295 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.295 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -1.5018 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | 0.1224 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 5 | 5 | -3.9444 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.6853 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 5 | 5 | -0.2946 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 4 | 4 | 2.2575 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 3 | 3 | -0.8875 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 0.2203 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 2 | 2 | -2.678 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 0.2238 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -2.8791 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.4063 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 1.0707 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.0559 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.44 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 1 | 1 | 4.666 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 327, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 4660 | 4611 | None | -1.1163 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4605 | 4556 | None | -1.0904 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3037 | 3026 | None | -0.8227 | 0.1527 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2508 | 2500 | None | -1.0292 | 0.066 | `hold_sample` |
| `ai_score_source` | `live` | 1491 | 1491 | None | -0.9479 | 0.1241 | `hold_sample` |
| `ai_score_band` | `score_70p` | 1098 | 1098 | None | -0.7728 | 0.1703 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 824 | 824 | None | -0.8003 | 0.2282 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 813 | 813 | None | -0.9346 | 0.0972 | `hold_sample` |
| `arm` | `PYRAMID` | 757 | 746 | None | 0.6386 | 0.9919 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 757 | 746 | None | 0.6386 | 0.9919 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 625 | 622 | None | -0.5517 | 0.2347 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 586 | 586 | None | 0.4266 | 0.9898 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 311 | 311 | None | -0.8006 | 0.164 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 183 | 183 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 127 | 127 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 117 | 117 | None | -1.06 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 107 | 107 | None | -0.76 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.69)` | 91 | 91 | None | -1.69 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 91 | 91 | None | -0.8368 | 0.033 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 79 | 79 | None | -0.86 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `stage` | `exit` | 9 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.295 | -0.3933 | 0.2222 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 16 | 8 | -0.3104 | -0.4138 | 0.25 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 14 | 7 | -0.494 | -0.6586 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 6 | -0.3388 | -0.4517 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | -0.265 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1987 | -0.265 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.8875 | -1.1833 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 6 | 3 | -0.8875 | -1.1833 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 2 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |

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
