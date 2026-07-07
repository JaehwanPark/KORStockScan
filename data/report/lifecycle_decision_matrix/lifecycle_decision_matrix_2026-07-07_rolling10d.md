# Lifecycle Decision Matrix - 2026-07-07

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-07_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `39802`
- source_rows_total: `70828`
- retained_rows: `39802`
- dropped_rows_by_source: `{}`
- joined_rows: `20086`
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
- lifecycle_flow_bucket_count: `247`
- lifecycle_flow_complete_count: `83`
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
| `entry` | 2369 | 207 | 1.0716 | 0.524 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 744 | 171 | -0.554 | 0.6357 | `pass` | `NO_CHANGE` | False |
| `holding` | 495 | 171 | -0.9487 | 0.809 | `pass` | `EXIT` | False |
| `scale_in` | 19298 | 19127 | -0.749 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 16896 | 410 | -0.9234 | 0.1575 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 247, 'complete_flow_count': 83, 'incomplete_flow_count': 37011, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 16247 | 16116 | -0.9839 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2798 | 2758 | 0.6283 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 217 | 217 | -1.03 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 94 | 94 | 1.0589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 41 | 41 | 2.0533 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 17 | 17 | 0.2018 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 16 | 16 | 2.4863 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 12 | 12 | -0.9808 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 5 | 5 | -2.7209 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.08 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 5 | 5 | -0.77 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 4 | 4 | -1.7356 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 12 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:97cbb762ac` | 2 | 2 | -2.4121 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df2241cc71` | 2 | 2 | -1.827 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 17 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 2 | 2 | -1.8977 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 396, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1610 | 201 | 1.1229 | 1.6787 | 0.5373 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 285 | 156 | 1.4374 | 2.4303 | 0.5705 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1342 | 152 | 0.7829 | 0.9644 | 0.5395 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2313 | 151 | 1.4802 | 2.4984 | 0.5629 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 365 | 79 | 1.9591 | 3.2691 | 0.6076 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 79 | 79 | 1.9591 | 3.2691 | 0.6076 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 176 | 61 | 1.8598 | 3.1589 | 0.6229 | `hold_no_edge` |
| `score_band` | `score_70p` | 352 | 59 | 0.8469 | 1.2072 | 0.5424 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1607 | 47 | 0.0492 | -0.8438 | 0.4468 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 462 | 46 | 0.9207 | 1.1499 | 0.4783 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 841 | 41 | -0.1498 | -0.8622 | 0.4878 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 418 | 40 | 1.4226 | 3.2735 | 0.65 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 763 | 37 | 0.251 | -0.1716 | 0.4595 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 31 | 31 | 0.4743 | 0.7558 | 0.4516 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 27 | 27 | -0.4574 | 2.2104 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 174 | 24 | 3.2751 | 6.2003 | 0.6667 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 279 | 21 | 0.095 | -1.8943 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 21 | 21 | 0.7008 | 0.9448 | 0.4286 | `hold_sample` |
| `score_band` | `score_63_65` | 109 | 21 | 1.8629 | 2.4779 | 0.6191 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 20 | 20 | 0.5264 | -3.6845 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 12 | 12 | 0.6964 | 0.8433 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 129, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 509 | 171 | -0.554 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 473 | 171 | -0.554 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 473 | 171 | -0.554 | `keep_collecting` |
| `latency_state` | `simulated` | 473 | 171 | -0.554 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 509 | 171 | -0.554 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 473 | 171 | -0.554 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 432 | 155 | -0.5816 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 707 | 154 | -0.6281 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 361 | 117 | -0.6839 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 317 | 110 | -0.2233 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 317 | 110 | -0.2233 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 298 | 100 | -0.2679 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 319 | 100 | -0.2679 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 298 | 100 | -0.2679 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 175 | 71 | -0.957 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 160 | 61 | -1.1505 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 156 | 61 | -1.1505 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 156 | 61 | -1.1505 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 154 | 56 | -1.3666 | `keep_collecting` |
| `would_limit_fill` | `true` | 149 | 56 | -0.2013 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 115 | 54 | -0.2725 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 125 | 53 | -0.9857 | `keep_collecting` |
| `would_limit_fill` | `false` | 420 | 44 | -0.3527 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 76 | 32 | -1.6623 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 124 | 31 | -0.3824 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 98 | 30 | -0.4012 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 51 | 26 | 0.0293 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 21 | 15 | 0.5721 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 37 | 13 | -0.5183 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 25 | 13 | -0.2818 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 45 | 12 | -0.7457 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 19 | 10 | 0.2234 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 35 | 8 | -0.6871 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 44, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 473 | 171 | -0.9487 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 473 | 171 | -0.9487 | `hold_no_edge` |
| `holding_action` | `WAIT` | 443 | 157 | -1.0399 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 101 | 91 | -2.1194 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 86 | 86 | -2.1339 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 32 | 29 | 0.052 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 25 | 25 | 0.8413 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 25 | 25 | -0.0183 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 22 | 22 | 0.7375 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 22 | 14 | -0.2379 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 14 | 14 | -0.2379 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 23 | 11 | 0.4351 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 10 | 10 | 1.1167 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 8 | 8 | 0.9434 | `hold_sample` |
| `holding_action` | `BUY` | 6 | 3 | -1.2478 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.7968 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 3 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.13 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.8099 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 1 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 22 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 302 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 286 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 61, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 261 | 261 | -0.9342 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 261 | 261 | -0.9342 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 261 | 261 | -0.9342 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 255 | 255 | -1.496 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 177 | 177 | -1.2473 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 127 | 127 | -0.9826 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 86 | 86 | -0.4629 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 72 | 72 | -0.5157 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 53 | 53 | -1.4447 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 49 | 49 | -1.9342 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 48 | 48 | 0.5479 | `candidate_recovery_or_relax` |
| `exit_outcome` | `MISSED_UPSIDE` | 41 | 41 | -0.6877 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 33 | 33 | -0.6068 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 30 | 30 | 0.28 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 16508 | 22 | -0.4541 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.4541 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.4541 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 20 | 20 | 0.6625 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 20 | 20 | -1.5499 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.539 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 14 | 14 | -3.381 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 12 | 1.6803 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 12 | 12 | -0.6555 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 11 | 11 | -1.6433 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 10 | 10 | -0.5304 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 10 | 10 | -1.0822 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.209 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | 0.1254 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -2.6078 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 0.8464 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | 0.2502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 6 | 6 | 1.1608 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 6 | 6 | 0.662 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 5 | 5 | 0.124 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 1.084 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -4.6142 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.8062 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 428, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 16802 | 16791 | None | -0.8169 | 0.1453 | `hold_sample` |
| `arm` | `AVG_DOWN` | 16481 | 16350 | None | -1.071 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 16286 | 16155 | None | -1.044 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 8062 | 8062 | None | -0.8416 | 0.1612 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4212 | 4212 | None | -0.7957 | 0.1427 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3333 | 3325 | None | -0.9734 | 0.0927 | `hold_sample` |
| `arm` | `PYRAMID` | 2817 | 2777 | None | 0.5818 | 0.9801 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2817 | 2777 | None | 0.5818 | 0.9801 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2474 | 2474 | None | 0.47 | 0.9778 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1958 | 1955 | None | -0.7222 | 0.1463 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1566 | 1566 | None | -0.7126 | 0.1399 | `hold_sample` |
| `ai_score_source` | `live` | 1491 | 1491 | None | -0.9479 | 0.1241 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 813 | 813 | None | -0.9346 | 0.0972 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 573 | 573 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 418 | 418 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 271 | 271 | None | -0.7696 | 0.0738 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 228 | 228 | None | -0.68 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 44 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 22 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 44 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `stage` | `exit` | 22 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 44 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 22 | 22 | -0.4541 | -0.6055 | 0.1818 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | -0.4823 | -0.643 | 0.2 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 36 | 18 | -0.6942 | -0.9256 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 13 | -0.1962 | -0.2615 | 0.3077 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0822 | -1.443 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 20 | 10 | -1.0822 | -1.443 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.209 | -0.2787 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.209 | -0.2787 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.9762 | -1.3016 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.8325 | 1.11 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 1 | 1 | 0.0075 | 0.01 | 1.0 | `hold_sample` |

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
