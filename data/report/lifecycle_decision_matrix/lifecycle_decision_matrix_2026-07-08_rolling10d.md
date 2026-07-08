# Lifecycle Decision Matrix - 2026-07-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-08_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `43411`
- source_rows_total: `75807`
- retained_rows: `43411`
- dropped_rows_by_source: `{}`
- joined_rows: `21556`
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
- lifecycle_flow_bucket_count: `277`
- lifecycle_flow_complete_count: `103`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0026`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2709 | 226 | 0.9602 | 0.4889 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 845 | 201 | -0.5375 | 0.6738 | `pass` | `NO_CHANGE` | False |
| `holding` | 573 | 201 | -1.0237 | 0.8375 | `pass` | `EXIT` | False |
| `scale_in` | 20671 | 20465 | -0.7598 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 18613 | 463 | -0.9575 | 0.1582 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 277, 'complete_flow_count': 103, 'incomplete_flow_count': 40187, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 17390 | 17229 | -0.9982 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 3007 | 2962 | 0.632 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 232 | 232 | -1.0266 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 97 | 97 | 0.9978 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 42 | 42 | 2.0011 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 19 | 19 | 0.1216 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 16 | 16 | 2.4863 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 14 | 14 | -0.9607 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.7667 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 5 | 5 | -2.7209 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.08 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 3 | 3 | -0.68 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 2 | 2 | -2.5496 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 16 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:97cbb762ac` | 2 | 2 | -2.4121 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 2 | 2 | -1.3398 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df2241cc71` | 2 | 2 | -1.827 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 410, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1865 | 220 | 1.004 | 1.3593 | 0.5045 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1578 | 168 | 0.6909 | 0.6583 | 0.5 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 301 | 159 | 1.4021 | 2.3742 | 0.5598 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2638 | 155 | 1.4233 | 2.4081 | 0.5484 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 404 | 83 | 1.8298 | 3.0633 | 0.5783 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 83 | 83 | 1.8298 | 3.0633 | 0.5783 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1889 | 62 | 0.0063 | -1.1939 | 0.3871 | `hold_no_edge` |
| `score_band` | `score_70p` | 368 | 62 | 0.7615 | 1.087 | 0.5161 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 186 | 62 | 1.8172 | 3.0561 | 0.6129 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1051 | 56 | -0.1439 | -1.2448 | 0.4107 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 569 | 50 | 0.8669 | 0.8866 | 0.44 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 989 | 49 | 0.2305 | -0.5919 | 0.3878 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 500 | 45 | 1.2104 | 2.4962 | 0.5778 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 33 | 33 | 0.41 | 0.6662 | 0.4242 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 32 | 32 | 0.2645 | -3.6453 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 30 | 30 | -0.4068 | 2.276 | 1.0 | `hold_sample` |
| `stale_bucket` | `fresh` | 365 | 29 | -0.0435 | -2.1124 | 0.2759 | `hold_sample` |
| `score_band` | `score_60_62` | 769 | 28 | -0.0115 | -1.3371 | 0.3214 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 183 | 24 | 3.2751 | 6.2003 | 0.6667 | `candidate_recovery_or_relax` |
| `strength_bucket` | `neutral_strength_momentum` | 251 | 23 | 1.0354 | 0.9384 | 0.4348 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 12 | 12 | 0.6964 | 0.8433 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 133, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 586 | 201 | -0.5375 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 547 | 201 | -0.5375 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 547 | 201 | -0.5375 | `keep_collecting` |
| `latency_state` | `simulated` | 547 | 201 | -0.5375 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 586 | 201 | -0.5375 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 545 | 199 | -0.4885 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 503 | 184 | -0.5675 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 808 | 184 | -0.598 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 428 | 144 | -0.5797 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 359 | 127 | -0.2086 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 359 | 127 | -0.2086 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 340 | 117 | -0.2456 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 364 | 117 | -0.2456 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 340 | 117 | -0.2456 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 207 | 84 | -0.9441 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 192 | 74 | -1.1019 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 188 | 74 | -1.1019 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 188 | 74 | -1.1019 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 186 | 69 | -1.2737 | `keep_collecting` |
| `would_limit_fill` | `true` | 173 | 65 | -0.1588 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 148 | 61 | -1.0217 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 120 | 55 | -0.2498 | `keep_collecting` |
| `would_limit_fill` | `false` | 465 | 52 | -0.354 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 142 | 39 | -0.378 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 120 | 39 | -0.2843 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 91 | 38 | -1.466 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 53 | 26 | 0.0293 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 59 | 17 | -0.6016 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 21 | 15 | 0.5721 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 40 | 14 | -0.4114 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 25 | 13 | -0.2818 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 47 | 12 | -0.375 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 19 | 10 | 0.2234 | `keep_collecting` |
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
| `held_bucket` | `held_not_applicable_at_start` | 547 | 201 | -1.0237 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 547 | 201 | -1.0237 | `hold_no_edge` |
| `holding_action` | `WAIT` | 515 | 187 | -1.1059 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 122 | 112 | -2.1306 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 107 | 107 | -2.1427 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 35 | 31 | 0.0685 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 28 | 28 | 0.6808 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 27 | 27 | 0.0059 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 25 | 25 | 0.5701 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 23 | 14 | -0.2379 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 14 | 14 | -0.2379 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 24 | 11 | 0.4351 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 11 | 11 | 1.3202 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.2114 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 5 | 0.096 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | 0.096 | `hold_sample` |
| `holding_action` | `BUY` | 6 | 3 | -1.2478 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.7968 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 1.8099 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 26 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 17 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 346 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 328 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 62, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 293 | 293 | -1.5317 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 284 | 284 | -0.9318 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 284 | 284 | -0.9318 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 284 | 284 | -0.9318 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 194 | 194 | -1.249 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 153 | 153 | -1.11 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 90 | 90 | -0.4685 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 76 | 76 | -0.5195 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 69 | 69 | -1.9382 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 63 | 63 | -1.6118 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 54 | 54 | -0.7738 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | 0.5773 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 36 | 36 | -0.736 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 32 | 32 | 0.2718 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 28 | 28 | -1.4826 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 27 | 27 | -2.5066 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 18176 | 26 | -0.341 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 26 | 26 | -0.341 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 26 | 26 | -0.341 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 23 | 23 | 0.4903 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 15 | 15 | -3.6088 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 14 | 14 | 1.9052 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.7534 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 12 | 12 | -0.6555 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 11 | 11 | -0.755 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 11 | 11 | 0.0893 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 10 | 10 | -1.0822 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.209 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -3.1316 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 0.8464 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.9002 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 7 | 7 | 1.4372 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 6 | 6 | 0.0933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 6 | 6 | 0.2502 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 6 | 6 | 0.662 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 1.084 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 5 | 5 | -4.6142 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 432, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 17643 | 17482 | None | -1.0925 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 17423 | 17262 | None | -1.0642 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 16960 | 16945 | None | -0.8188 | 0.1448 | `hold_sample` |
| `ai_score_band` | `score_70p` | 8065 | 8064 | None | -0.8413 | 0.1614 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4524 | 4513 | None | -1.0239 | 0.0973 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4228 | 4228 | None | -0.794 | 0.1447 | `hold_sample` |
| `arm` | `PYRAMID` | 3028 | 2983 | None | 0.5864 | 0.9802 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 3028 | 2983 | None | 0.5864 | 0.9802 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2614 | 2614 | None | 0.464 | 0.9778 | `hold_sample` |
| `ai_score_source` | `live` | 2326 | 2326 | None | -1.0111 | 0.1307 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2077 | 2074 | None | -0.7062 | 0.1637 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1577 | 1577 | None | -0.7141 | 0.1408 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1130 | 1130 | None | -0.9803 | 0.1142 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 602 | 602 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 434 | 434 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 302 | 302 | None | -0.8097 | 0.0762 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 239 | 239 | None | -0.4621 | 0.2887 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 52 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 26 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 52 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `stage` | `exit` | 26 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 52 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 26 | 26 | -0.341 | -0.4546 | 0.2692 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 48 | 24 | -0.355 | -0.4733 | 0.2917 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 38 | 19 | -0.6616 | -0.8821 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 34 | 17 | -0.0838 | -0.1118 | 0.4118 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0822 | -1.443 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 20 | 10 | -1.0822 | -1.443 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 9 | 9 | -0.1942 | -0.2589 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 18 | 9 | -0.1942 | -0.2589 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.9762 | -1.3016 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.8644 | 1.1525 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.8644 | 1.1525 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.8644 | 1.1525 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |

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
