# Lifecycle Decision Matrix - 2026-07-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-08_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `29788`
- source_rows_total: `47656`
- retained_rows: `29788`
- dropped_rows_by_source: `{}`
- joined_rows: `14258`
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
- lifecycle_flow_bucket_count: `217`
- lifecycle_flow_complete_count: `74`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0027`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1654 | 107 | 1.0394 | 0.1432 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 636 | 133 | -0.6422 | 0.5374 | `pass` | `NO_CHANGE` | False |
| `holding` | 430 | 133 | -1.2249 | 0.7544 | `pass` | `EXIT` | False |
| `scale_in` | 13689 | 13545 | -0.7137 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 13379 | 340 | -1.0266 | 0.1536 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 217, 'complete_flow_count': 74, 'incomplete_flow_count': 27606, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 11428 | 11311 | -0.953 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2058 | 2031 | 0.6328 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 178 | 178 | -1.0151 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 40 | 40 | 0.915 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 13 | 13 | 4.4797 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 11 | 11 | 0.3369 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.9509 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.82 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 3 | 3 | -1.3367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 2 | 2 | -2.5496 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 15 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 2 | 2 | -1.3398 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 15 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:b0018089a8` | 2 | 2 | -1.8977 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.6351 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 331, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1050 | 101 | 1.1395 | 1.2152 | 0.4455 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 939 | 81 | 0.5191 | -0.2075 | 0.3951 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 186 | 63 | 1.9047 | 3.1805 | 0.5714 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1606 | 59 | 1.9946 | 3.3243 | 0.5424 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 318 | 59 | 1.9946 | 3.3243 | 0.5424 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 59 | 59 | 1.9946 | 3.3243 | 0.5424 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 272 | 51 | 0.6987 | 1.0078 | 0.5098 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 944 | 48 | -0.1346 | -1.4563 | 0.375 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 152 | 44 | 2.4671 | 4.0808 | 0.6136 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 504 | 42 | 0.7275 | 0.5255 | 0.381 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 1087 | 40 | -0.0281 | -1.795 | 0.3 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 899 | 40 | 0.1608 | -1.0779 | 0.325 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 420 | 30 | 1.5804 | 2.9015 | 0.5333 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 329 | 26 | 0.0424 | -2.4331 | 0.2308 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | 0.1302 | -3.61 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 685 | 22 | 0.0435 | -1.6032 | 0.2727 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 215 | 18 | 0.0104 | -0.7048 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 18 | 18 | -0.5558 | 2.2017 | 1.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 251 | 18 | 0.3194 | -1.003 | 0.3333 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 17 | 17 | 0.0769 | 0.0666 | 0.4118 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 117, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 435 | 133 | -0.6422 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 412 | 133 | -0.6422 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 412 | 133 | -0.6422 | `keep_collecting` |
| `latency_state` | `simulated` | 412 | 133 | -0.6422 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 435 | 133 | -0.6422 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 632 | 132 | -0.6472 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 410 | 131 | -0.5694 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 379 | 121 | -0.7121 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 340 | 99 | -0.672 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 256 | 75 | -0.237 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 256 | 75 | -0.237 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 252 | 74 | -0.2403 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 273 | 74 | -0.2403 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 252 | 74 | -0.2403 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 159 | 59 | -1.1463 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 160 | 59 | -1.1463 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 158 | 58 | -1.1663 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 156 | 58 | -1.1663 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 156 | 58 | -1.1663 | `keep_collecting` |
| `would_limit_fill` | `true` | 125 | 40 | -0.2168 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 111 | 39 | -1.3729 | `keep_collecting` |
| `would_limit_fill` | `false` | 351 | 34 | -0.2679 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 78 | 33 | -1.3595 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 71 | 32 | -0.2522 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 103 | 29 | -0.1954 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 109 | 24 | -0.3015 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 52 | 15 | -0.5284 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 22 | 11 | -0.2732 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 43 | 11 | -0.5154 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 10 | -0.1872 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 29 | 9 | -0.1558 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 190 | 5 | -1.233 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 5 | -0.0276 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 4 | -0.7665 | `source_quality_workorder` |
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
| `held_bucket` | `held_not_applicable_at_start` | 412 | 133 | -1.2249 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 412 | 133 | -1.2249 | `hold_no_edge` |
| `holding_action` | `WAIT` | 384 | 122 | -1.3306 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 92 | 84 | -2.1359 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 80 | 80 | -2.1482 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 21 | 19 | 0.03 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 0.464 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | -0.0037 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 16 | 16 | 0.2505 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 21 | 9 | 0.1537 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 7 | 4 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 4 | 4 | 1.9299 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.2767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.0561 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 279 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 18 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 262 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 58, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 232 | 232 | -1.5028 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 213 | 213 | -0.9386 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 213 | 213 | -0.9386 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 213 | 213 | -0.9386 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 153 | 153 | -1.2103 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 109 | 109 | -1.3031 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 57 | 57 | -1.9834 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 55 | 55 | -0.4961 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 51 | 51 | -0.5194 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 47 | 47 | -1.7667 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 43 | 43 | -0.8938 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 35 | 35 | 0.4773 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 24 | 24 | -2.4955 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 24 | 24 | -1.512 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 22 | 22 | 0.158 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 19 | 19 | -1.0828 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 13057 | 18 | -0.3938 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.3938 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.3938 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 16 | 16 | 0.357 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.6304 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 9 | 9 | -3.8243 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 9 | 9 | -1.8751 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 8 | 0.0765 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 8 | 8 | -1.0275 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 2.4404 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 6 | 6 | 1.2868 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -3.4667 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 0.6218 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1987 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.11 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 3 | 3 | -0.1727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 3 | 3 | 1.4522 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 388, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 11619 | 11502 | None | -1.0624 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 11494 | 11377 | None | -1.0382 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10042 | 10027 | None | -0.752 | 0.1536 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4340 | 4329 | None | -1.0221 | 0.0975 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3506 | 3505 | None | -0.7637 | 0.1769 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2729 | 2729 | None | -0.7035 | 0.1722 | `hold_sample` |
| `ai_score_source` | `live` | 2326 | 2326 | None | -1.0111 | 0.1307 | `hold_sample` |
| `arm` | `PYRAMID` | 2070 | 2043 | None | 0.5889 | 0.9828 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2070 | 2043 | None | 0.5889 | 0.9828 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1734 | 1734 | None | 0.4393 | 0.9804 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1675 | 1672 | None | -0.662 | 0.1767 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1303 | 1303 | None | -0.6834 | 0.1481 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1130 | 1130 | None | -0.9803 | 0.1142 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 450 | 450 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 386 | 386 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 228 | 228 | None | -0.8432 | 0.0614 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.39)` | 197 | 197 | None | -0.39 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 196 | 196 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 180 | 180 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 174 | 174 | None | -0.4928 | 0.2816 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 36 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 18 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 36 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `stage` | `exit` | 18 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 36 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 18 | 18 | -0.3938 | -0.525 | 0.2778 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 34 | 17 | -0.4068 | -0.5424 | 0.2941 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 26 | 13 | -0.6992 | -0.9323 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 20 | 10 | -0.0908 | -0.121 | 0.5 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 8 | 8 | -1.0275 | -1.37 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 16 | 8 | -1.0275 | -1.37 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.9195 | -1.226 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 4 | 2 | -0.3975 | -0.53 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8775 | 1.17 | 1.0 | `hold_sample` |

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
