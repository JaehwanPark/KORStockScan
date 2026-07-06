# Lifecycle Decision Matrix - 2026-07-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-06_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `14804`
- source_rows_total: `23189`
- retained_rows: `14804`
- dropped_rows_by_source: `{}`
- joined_rows: `7691`
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
- lifecycle_flow_complete_count: `29`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0021`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 737 | 51 | 1.4357 | 0.1318 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 333 | 60 | -0.8011 | 0.3932 | `pass` | `NO_CHANGE` | False |
| `holding` | 227 | 60 | -1.4732 | 0.6089 | `pass` | `EXIT` | False |
| `scale_in` | 7396 | 7342 | -0.726 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6111 | 178 | -1.1097 | 0.1787 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 133, 'complete_flow_count': 29, 'incomplete_flow_count': 13781, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 6175 | 6124 | -0.9542 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1106 | 1103 | 0.5568 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 106 | 106 | -1.0405 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 25 | 25 | 0.5604 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 6 | 6 | 7.1604 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 6 | 6 | -1.1834 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 4 | 4 | 2.8398 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.9659 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 3 | 3 | 0.1767 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 7 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.6351 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 1 | 1 | -2.4958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:dfd7c31acb` | 1 | 1 | -1.5916 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 1 | 1 | -1.8771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5753169481` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:737c4560d0` | 1 | 1 | -2.2711 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 1 | 1 | -0.5483 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 1 | 1 | -1.654 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 237, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 455 | 51 | 1.4357 | 1.3755 | 0.451 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 415 | 45 | 0.9608 | 0.6413 | 0.4444 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 72 | 35 | 1.9523 | 3.0734 | 0.5428 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 721 | 35 | 1.9523 | 3.0734 | 0.5428 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 191 | 35 | 1.9523 | 3.0734 | 0.5428 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 35 | 35 | 1.9523 | 3.0734 | 0.5428 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 151 | 29 | 0.6402 | 0.439 | 0.4483 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 208 | 25 | 1.373 | 1.9054 | 0.44 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 89 | 24 | 2.3299 | 3.6304 | 0.5833 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 383 | 21 | 0.2829 | -1.2223 | 0.2857 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 451 | 16 | 0.3058 | -2.3388 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 377 | 16 | 0.3058 | -2.3388 | 0.25 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 161 | 14 | 0.2686 | -2.4329 | 0.2857 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 11 | 0.2573 | 0.3264 | 0.3636 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 236 | 10 | 2.6646 | 3.7796 | 0.8 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 195 | 9 | 0.787 | 0.3059 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 8 | 8 | 0.7664 | -3.7587 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 52 | 8 | 1.2029 | 0.6471 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 7 | 7 | 0.9605 | 1.4162 | 0.4286 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 98 | 7 | 0.7382 | -2.5766 | 0.1429 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 232 | 60 | -0.8011 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 221 | 60 | -0.8011 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 221 | 60 | -0.8011 | `keep_collecting` |
| `latency_state` | `simulated` | 221 | 60 | -0.8011 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 232 | 60 | -0.8011 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 221 | 60 | -0.8011 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 329 | 59 | -0.8148 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 203 | 55 | -0.8073 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 184 | 46 | -0.8055 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 101 | 33 | -1.3795 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 102 | 33 | -1.3795 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 100 | 32 | -1.4229 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 98 | 32 | -1.4229 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 98 | 32 | -1.4229 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 123 | 28 | -0.0904 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 123 | 28 | -0.0904 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 119 | 27 | -0.0941 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 128 | 27 | -0.0941 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 119 | 27 | -0.0941 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 67 | 24 | -1.4947 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 49 | 21 | -1.5897 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 177 | 14 | -0.1458 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 38 | 14 | -0.7864 | `keep_collecting` |
| `would_limit_fill` | `true` | 54 | 13 | -0.0384 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 56 | 10 | 0.0143 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 49 | 10 | 0.0376 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 17 | 5 | -0.733 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 28 | 5 | -0.2606 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 105 | 4 | -2.0866 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 9 | 4 | -0.546 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 5 | 3 | -0.2919 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 3 | -0.367 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -1.7491 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 16 | 3 | -0.8304 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 4 | 1 | 0.01 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 221 | 60 | -1.4732 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 221 | 60 | -1.4732 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 204 | 55 | -1.5518 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 44 | 42 | -2.1481 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 39 | 39 | -2.1635 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 11 | 10 | 0.0796 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 9 | 9 | -0.0505 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.0596 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | -0.0596 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 14 | 4 | -0.3788 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -2.1584 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -1.5266 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 1 | 0.01 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 1 | -0.23 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 1 | 1 | 1.5514 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.01 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 161 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 149 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 126 | 126 | -1.4893 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 120 | 120 | -1.0147 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 120 | 120 | -1.0147 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 120 | 120 | -1.0147 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 88 | 88 | -1.2374 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 52 | 52 | -1.4353 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 31 | 31 | -0.4972 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 29 | 29 | -0.5197 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | -2.1033 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 22 | 22 | -1.1982 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 20 | 20 | -1.8019 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | 0.2168 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -1.7254 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 12 | 12 | 0.2301 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 10 | 10 | -1.2243 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 10 | 10 | -2.6619 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 5939 | 6 | -0.1888 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1888 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1888 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 5 | 5 | -0.0596 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 5 | 5 | -2.9426 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -1.2339 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.9432 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -2.9017 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -1.879 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 2 | 2 | -2.678 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.0112 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 2 | 2 | 1.5477 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.795 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 2 | 2 | 1.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.0039 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | -0.1859 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | 0.0559 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | -0.03 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -4.7992 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 311, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 6286 | 6235 | None | -1.0432 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 6225 | 6174 | None | -1.0212 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 6177 | 6174 | None | -0.8081 | 0.1505 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 1942 | 1942 | None | -0.7426 | 0.1833 | `hold_sample` |
| `ai_score_band` | `score_70p` | 1926 | 1926 | None | -0.9283 | 0.1531 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1510 | 1509 | None | -0.9803 | 0.0663 | `hold_sample` |
| `arm` | `PYRAMID` | 1110 | 1107 | None | 0.5253 | 0.9946 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1110 | 1107 | None | 0.5253 | 0.9946 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1072 | 1070 | None | -0.5884 | 0.1972 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 991 | 991 | None | 0.4443 | 0.994 | `hold_sample` |
| `ai_score_source` | `live` | 924 | 924 | None | -0.7833 | 0.1504 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 892 | 892 | None | -0.6572 | 0.1514 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 267 | 267 | None | -0.23 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 229 | 229 | None | -0.9303 | 0.1048 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 133 | 133 | None | -1.06 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 128 | 128 | None | -0.815 | 0.0391 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.65)` | 113 | 113 | None | -0.65 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 110 | 110 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.44)` | 106 | 106 | None | -0.44 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 103 | 103 | None | -0.76 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 28, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 12 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 6 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 12 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `stage` | `exit` | 6 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 12 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1888 | -0.2517 | 0.3333 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 10 | 5 | -0.192 | -0.256 | 0.4 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.0844 | -0.1125 | 0.5 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.4838 | -0.645 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.795 | -1.06 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -0.795 | -1.06 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.795 | 1.06 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
