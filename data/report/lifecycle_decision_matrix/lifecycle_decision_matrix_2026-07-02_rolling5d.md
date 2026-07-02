# Lifecycle Decision Matrix - 2026-07-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-02_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `27597`
- source_rows_total: `52017`
- retained_rows: `27597`
- dropped_rows_by_source: `{}`
- joined_rows: `14402`
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
- lifecycle_flow_bucket_count: `188`
- lifecycle_flow_complete_count: `49`
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
| `entry` | 1628 | 162 | 1.0976 | 0.6358 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 468 | 107 | -0.4699 | 0.7068 | `pass` | `NO_CHANGE` | False |
| `holding` | 315 | 107 | -0.7159 | 0.8043 | `pass` | `EXIT` | False |
| `scale_in` | 13881 | 13770 | -0.7433 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 11305 | 256 | -0.8513 | 0.1613 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 188, 'complete_flow_count': 49, 'incomplete_flow_count': 25767, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 11673 | 11591 | -0.979 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2045 | 2016 | 0.6145 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 139 | 139 | -1.0254 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 77 | 77 | 1.2075 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 34 | 34 | 1.6335 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 14 | 14 | 0.0453 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 13 | 13 | 2.1866 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 6 | 6 | -1.2167 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df02034b40` | 10 | 2 | -1.24 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -2.1328 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 2 | 2 | -2.7092 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:7d1a415bd0` | 2 | 2 | 0.8157 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 2 | 2 | -0.695 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 2 | 2 | -0.66 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 1 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce511c4ca6` | 1 | 1 | -1.4427 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:65ec45aaab` | 1 | 1 | -1.6151 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a5aac23c60` | 1 | 1 | -0.115 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 347, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1123 | 157 | 1.1578 | 1.8634 | 0.5477 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 205 | 128 | 1.3875 | 2.3826 | 0.5547 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1590 | 124 | 1.4269 | 2.4527 | 0.5484 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 899 | 114 | 0.7847 | 1.1864 | 0.5526 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 233 | 52 | 2.081 | 3.5603 | 0.5962 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 52 | 52 | 2.081 | 3.5603 | 0.5962 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 107 | 46 | 1.7129 | 2.9154 | 0.5869 | `hold_no_edge` |
| `score_band` | `score_70p` | 244 | 38 | 1.0507 | 1.7308 | 0.5 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 237 | 36 | 1.5486 | 3.673 | 0.6667 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1105 | 30 | 0.1651 | -0.3797 | 0.5333 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 25 | 25 | 0.6749 | 1.066 | 0.44 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 413 | 23 | -0.1555 | -0.3522 | 0.6087 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 243 | 22 | 0.9495 | 1.2729 | 0.5455 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 136 | 21 | 2.8636 | 5.3951 | 0.6667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 21 | 21 | -0.4423 | 2.1319 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 18 | 18 | 0.7091 | 1.0028 | 0.3889 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 344 | 18 | 0.3491 | 0.3587 | 0.5556 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 210 | 14 | 1.2181 | 0.11 | 0.3571 | `hold_sample` |
| `score_band` | `score_63_65` | 73 | 13 | 2.5462 | 3.8415 | 0.6923 | `hold_sample` |
| `score_band` | `score_66_69` | 41 | 12 | 2.2655 | 5.4181 | 0.8333 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.9273 | 1.1505 | 0.8 | `candidate_recovery_or_relax` |

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
| `actual_order_submitted` | `false` | 326 | 107 | -0.4699 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 302 | 107 | -0.4699 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 302 | 107 | -0.4699 | `keep_collecting` |
| `latency_state` | `simulated` | 302 | 107 | -0.4699 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 326 | 107 | -0.4699 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 302 | 107 | -0.4699 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 271 | 95 | -0.5286 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 432 | 91 | -0.5743 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 216 | 78 | -0.1977 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 216 | 78 | -0.1977 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 198 | 69 | -0.2557 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 208 | 69 | -0.2557 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 198 | 69 | -0.2557 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 219 | 68 | -0.6427 | `keep_collecting` |
| `would_limit_fill` | `true` | 98 | 40 | -0.107 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 85 | 39 | -0.1686 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 104 | 38 | -0.8588 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 80 | 34 | -0.7692 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 89 | 29 | -1.202 | `keep_collecting` |
| `would_limit_fill` | `false` | 266 | 29 | -0.4607 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 86 | 29 | -1.202 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 86 | 29 | -1.202 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 84 | 23 | -1.792 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 44 | 22 | 0.081 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 82 | 20 | -0.7245 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 54 | 18 | -0.3369 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 20 | 15 | 0.5721 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 47 | 15 | -1.9979 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 28 | 9 | -0.2454 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 18 | 9 | 0.2472 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 18 | 9 | 0.1253 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | 0.0094 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 4 | -0.4088 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 302 | 107 | -0.7159 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 302 | 107 | -0.7159 | `hold_no_edge` |
| `holding_action` | `WAIT` | 284 | 97 | -0.8057 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 56 | 49 | -2.0552 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 45 | 45 | -2.0942 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 22 | 20 | -0.0373 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 1.0683 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 18 | 18 | -0.1048 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 16 | 16 | 0.9681 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 15 | 11 | -0.2273 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.2273 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 15 | 8 | 0.6087 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 0.9718 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 0.7891 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 3 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.6583 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.5735 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 13 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 195 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 187 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 166 | 166 | -0.9232 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 166 | 166 | -0.9232 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 166 | 166 | -0.9232 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 151 | 151 | -1.4691 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 109 | 109 | -1.2617 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 77 | 77 | -0.7446 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 57 | 57 | -0.4663 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 47 | 47 | -0.5253 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 33 | 33 | 0.5911 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 28 | 28 | -1.1964 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 28 | 28 | -0.5382 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 26 | 26 | -1.8666 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 21 | 21 | -0.4178 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 21 | 21 | 0.3053 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 14 | 14 | 0.8939 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 11062 | 13 | -0.5642 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.5642 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.5642 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 13 | 13 | -1.5758 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 9 | 9 | -3.0679 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 8 | 8 | 0.0065 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 1.3917 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 7 | 7 | -1.1657 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 7 | 7 | -2.628 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.9134 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 6 | 6 | -1.6083 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | 0.086 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 1.084 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -2.4993 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | 0.1853 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 0.6224 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.8062 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 4 | 4 | 0.045 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 1.2059 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.9978 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 1.1036 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8512 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 2 | 2 | 0.0238 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 347, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 13765 | 13765 | None | -0.8157 | 0.1436 | `hold_sample` |
| `arm` | `AVG_DOWN` | 11821 | 11739 | None | -1.0532 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 11681 | 11599 | None | -1.0257 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 6964 | 6964 | None | -0.8524 | 0.1598 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3388 | 3388 | None | -0.7946 | 0.1219 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `arm` | `PYRAMID` | 2060 | 2031 | None | 0.561 | 0.9758 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2060 | 2031 | None | 0.561 | 0.9758 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1888 | 1888 | None | 0.4834 | 0.974 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1333 | 1333 | None | -0.8018 | 0.105 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1255 | 1255 | None | -0.6908 | 0.1339 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 825 | 825 | None | -0.8042 | 0.1734 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 396 | 396 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 390 | 390 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 214 | 214 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 202 | 202 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.68)` | 202 | 202 | None | -1.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 192 | 192 | None | -0.89 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 26 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 13 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 26 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `stage` | `exit` | 13 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 26 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.5642 | -0.7523 | 0.1538 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 24 | 12 | -0.5969 | -0.7958 | 0.1667 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 22 | 11 | -0.8216 | -1.0955 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 7 | 7 | -1.1657 | -1.5543 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 7 | -0.0739 | -0.0986 | 0.2857 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 14 | 7 | -1.1657 | -1.5543 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.3519 | -1.8025 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.6225 | -0.83 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |

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
