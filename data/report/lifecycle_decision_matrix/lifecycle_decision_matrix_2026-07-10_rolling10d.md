# Lifecycle Decision Matrix - 2026-07-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-10_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `32654`
- source_rows_total: `51556`
- retained_rows: `32654`
- dropped_rows_by_source: `{}`
- joined_rows: `15523`
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
- lifecycle_flow_bucket_count: `253`
- lifecycle_flow_complete_count: `90`
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
| `entry` | 2269 | 119 | 0.9364 | 0.1301 | `pass` | `NO_CHANGE` | False |
| `submit` | 759 | 153 | -0.6299 | 0.5019 | `pass` | `NO_CHANGE` | False |
| `holding` | 493 | 153 | -1.1887 | 0.7214 | `pass` | `EXIT` | False |
| `scale_in` | 14915 | 14724 | -0.7159 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14218 | 374 | -1.0173 | 0.1486 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 253, 'complete_flow_count': 90, 'incomplete_flow_count': 29860, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 12482 | 12326 | -0.9519 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2217 | 2182 | 0.6317 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 187 | 187 | -1.02 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
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
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 2 | 2 | -1.6292 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 16 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 2 | 2 | -0.5731 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 2 | 2 | -1.3398 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 20 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 2 | 2 | -1.8977 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 367, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1378 | 110 | 1.0756 | 1.1634 | 0.4727 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1255 | 89 | 0.4964 | -0.0868 | 0.4382 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 363 | 66 | 1.8252 | 3.045 | 0.5909 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2212 | 62 | 1.9216 | 3.1863 | 0.5645 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 332 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 62 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1397 | 57 | -0.1352 | -1.2598 | 0.421 | `source_quality_workorder` |
| `score_band` | `score_70p` | 396 | 57 | 0.5981 | 0.826 | 0.5439 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 698 | 48 | 0.6237 | 0.6571 | 0.4583 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 227 | 47 | 2.3042 | 3.8975 | 0.6383 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1482 | 46 | 0.0139 | -1.4778 | 0.3478 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1114 | 43 | 0.2396 | -1.0915 | 0.3256 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 547 | 32 | 1.3726 | 2.5276 | 0.5312 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 505 | 28 | 0.0294 | -2.2382 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 27 | 27 | 0.1656 | -3.6189 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 880 | 27 | 0.0135 | -1.2252 | 0.3333 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 528 | 24 | -0.1337 | -0.5411 | 0.4583 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 24 | 24 | -0.3951 | 2.0558 | 1.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 432 | 22 | 0.4579 | -0.9934 | 0.3636 | `source_quality_workorder` |
| `stale_bucket` | `stale_high` | 885 | 21 | -0.2342 | -0.6229 | 0.4762 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 128, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 531 | 153 | -0.6299 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 472 | 153 | -0.6299 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 472 | 153 | -0.6299 | `keep_collecting` |
| `latency_state` | `simulated` | 472 | 153 | -0.6299 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 531 | 153 | -0.6299 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 748 | 152 | -0.6341 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 469 | 150 | -0.5647 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 436 | 139 | -0.6971 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 395 | 115 | -0.6076 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 295 | 85 | -0.2329 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 295 | 85 | -0.2329 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 291 | 84 | -0.2358 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 347 | 84 | -0.2358 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 291 | 84 | -0.2358 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 180 | 69 | -1.1097 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 181 | 69 | -1.1097 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 179 | 68 | -1.1262 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 177 | 68 | -1.1262 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 177 | 68 | -1.1262 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 127 | 43 | -1.2524 | `keep_collecting` |
| `would_limit_fill` | `true` | 140 | 43 | -0.3011 | `keep_collecting` |
| `would_limit_fill` | `false` | 438 | 41 | -0.1673 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 82 | 36 | -1.231 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 75 | 35 | -0.4236 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 133 | 31 | -0.1609 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 116 | 30 | -0.1961 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 68 | 21 | -0.7881 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 16 | -0.7252 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 24 | 13 | -0.5437 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 31 | 10 | -0.2116 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 10 | -0.1872 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 206 | 5 | -1.233 | `keep_collecting` |
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
| `held_bucket` | `held_not_applicable_at_start` | 472 | 153 | -1.1887 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 472 | 153 | -1.1887 | `hold_no_edge` |
| `holding_action` | `WAIT` | 443 | 141 | -1.2891 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 105 | 95 | -2.1433 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 91 | 91 | -2.1544 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 21 | 21 | 0.5767 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 22 | 20 | 0.0392 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 18 | 18 | 0.4057 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.0091 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 21 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 11 | 8 | -0.0553 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.1282 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 9 | 3 | -0.2767 | `hold_sample` |
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
| `holding_action` | `SELL_TODAY` | 21 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 319 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 21 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 302 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 251 | 251 | -1.5276 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 226 | 226 | -0.9421 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 161 | 161 | -1.2204 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 127 | 127 | -1.2449 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 63 | 63 | -1.9894 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 60 | 60 | -0.4925 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 55 | 55 | -0.5196 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 53 | 53 | -0.8531 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 52 | 52 | -1.6472 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 44 | 44 | 0.4986 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 27 | 27 | -1.5318 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 26 | 26 | -2.4916 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 23 | 23 | 0.1604 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 22 | 22 | -1.2379 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 13060 | 21 | -0.4497 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 21 | 21 | -0.4497 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 21 | 21 | -0.4497 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 18 | 18 | 0.5003 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | 0.0254 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | -3.8938 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 10 | 10 | -1.0402 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.9198 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.6304 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 2.1642 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.3769 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -3.4922 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 0.554 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.7144 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.1935 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.166 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.3504 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -3.6004 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 451, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 12684 | 12528 | None | -1.0649 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 12548 | 12392 | None | -1.0409 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10220 | 10198 | None | -0.7544 | 0.1536 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 5422 | 5404 | None | -0.9998 | 0.0976 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3509 | 3508 | None | -0.7648 | 0.1767 | `hold_sample` |
| `ai_score_source` | `live` | 2940 | 2940 | None | -1.0181 | 0.1272 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2744 | 2744 | None | -0.7044 | 0.1735 | `hold_sample` |
| `arm` | `PYRAMID` | 2231 | 2196 | None | 0.5901 | 0.9826 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2231 | 2196 | None | 0.5901 | 0.9826 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1828 | 1828 | None | 0.4391 | 0.9808 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1736 | 1733 | None | -0.6484 | 0.1866 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1504 | 1504 | None | -0.8925 | 0.1164 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1326 | 1326 | None | -0.6845 | 0.1524 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 918 | 918 | None | -1.0505 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 733 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `qty_reason` | `qty_none` | 696 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 735 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `time_bucket` | `time_unknown` | 735 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 551 | 551 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 432 | 432 | None | -1.0188 | 0.0995 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 42 | 21 | -0.4497 | -0.5995 | 0.2381 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 21 | 21 | -0.4497 | -0.5995 | 0.2381 | `hold_sample` |
| `stage` | `exit` | 21 | 21 | -0.4497 | -0.5995 | 0.2381 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 42 | 21 | -0.4497 | -0.5995 | 0.2381 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 21 | 21 | -0.4497 | -0.5995 | 0.2381 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | -0.4148 | -0.553 | 0.25 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 38 | 19 | -0.4788 | -0.6384 | 0.2632 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 32 | 16 | -0.7153 | -0.9537 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 24 | 12 | -0.2575 | -0.3433 | 0.4167 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 20 | 10 | -1.0402 | -1.387 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 9 | 9 | -1.0283 | -1.3711 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.9195 | -1.226 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
