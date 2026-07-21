# Lifecycle Decision Matrix - 2026-07-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-21_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `36465`
- source_rows_total: `60822`
- retained_rows: `36465`
- dropped_rows_by_source: `{}`
- joined_rows: `17458`
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
- lifecycle_flow_bucket_count: `313`
- lifecycle_flow_complete_count: `143`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0044`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3518 | 134 | 0.7896 | 0.1179 | `pass` | `NO_CHANGE` | False |
| `submit` | 1072 | 176 | -0.5852 | 0.4556 | `pass` | `NO_CHANGE` | False |
| `holding` | 573 | 176 | -1.1544 | 0.6702 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 16703 | 16509 | -0.7349 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 14599 | 463 | -0.9947 | 0.2533 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 313, 'complete_flow_count': 143, 'incomplete_flow_count': 32434, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14123 | 13964 | -0.9605 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2350 | 2315 | 0.6399 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 200 | 200 | -1.0198 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 43 | 43 | 0.8851 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 13 | 13 | 4.4797 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 13 | 13 | 0.2535 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.9509 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 7 | 7 | -0.8914 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 6 | 6 | 3.8073 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.308 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 4 | 4 | -2.794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 4 | 4 | -0.82 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 391, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1717 | 120 | 0.9937 | 0.9279 | 0.4667 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1627 | 98 | 0.467 | -0.1973 | 0.4388 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2420 | 72 | -0.1852 | -1.2864 | 0.4305 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 931 | 69 | 1.6636 | 2.8845 | 0.5942 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3446 | 62 | 1.9216 | 3.1863 | 0.5645 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 396 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 62 | 62 | 1.9216 | 3.1863 | 0.5645 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 501 | 61 | 0.4727 | 0.6824 | 0.541 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2043 | 56 | 0.0279 | -1.5109 | 0.3571 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1137 | 54 | 0.5115 | 0.5548 | 0.4815 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1399 | 53 | 0.1876 | -1.1946 | 0.3396 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 291 | 49 | 2.2161 | 3.5942 | 0.6122 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 858 | 35 | 1.1243 | 2.245 | 0.5429 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 33 | 33 | 0.1957 | -3.6042 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 1025 | 32 | -0.0177 | -1.2816 | 0.3438 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 31 | 31 | -0.5422 | 1.8265 | 1.0 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 586 | 30 | 0.1091 | -2.3477 | 0.2333 | `hold_sample` |
| `stale_bucket` | `stale_high` | 1221 | 30 | -0.2926 | -0.7283 | 0.5 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 596 | 28 | 0.4046 | -1.3848 | 0.3214 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 1186 | 27 | -0.3249 | -0.3832 | 0.5185 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 139, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 799 | 176 | -0.5852 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 546 | 176 | -0.5852 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 546 | 176 | -0.5852 | `keep_collecting` |
| `latency_state` | `simulated` | 546 | 176 | -0.5852 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 799 | 176 | -0.5852 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 1040 | 175 | -0.5886 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 543 | 173 | -0.5279 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 507 | 160 | -0.6548 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 458 | 132 | -0.5773 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 340 | 101 | -0.2644 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 340 | 101 | -0.2644 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 335 | 100 | -0.2671 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 581 | 100 | -0.2671 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 335 | 100 | -0.2671 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 209 | 76 | -1.0038 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 211 | 76 | -1.0038 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 208 | 75 | -1.0173 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 206 | 75 | -1.0173 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 206 | 75 | -1.0173 | `keep_collecting` |
| `would_limit_fill` | `false` | 703 | 51 | -0.1512 | `keep_collecting` |
| `would_limit_fill` | `true` | 158 | 49 | -0.3878 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 154 | 46 | -1.2485 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 86 | 41 | -0.3688 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 156 | 39 | -0.1819 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 89 | 39 | -1.2279 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 130 | 33 | -0.1898 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 89 | 24 | -0.7006 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 75 | 19 | -0.6246 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 28 | 16 | -0.7962 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 34 | 12 | -0.0715 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 21 | 12 | -0.0511 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 235 | 6 | -0.3409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 5 | 0.2108 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 5 | -0.0276 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 5 | 4 | 0.6577 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 546 | 176 | -1.1544 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 546 | 176 | -1.1544 | `hold_no_edge` |
| `holding_action` | `WAIT` | 515 | 163 | -1.2405 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 119 | 108 | -2.0843 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 103 | 103 | -2.1038 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 27 | 25 | -0.0225 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 22 | 22 | 0.6072 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 22 | 22 | -0.0541 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.45 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 14 | 11 | 0.0399 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 23 | 10 | 0.0528 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.0016 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 15 | 4 | -0.3537 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3537 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 4 | 4 | -1.7221 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.5281 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 27 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 370 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 352 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 13 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 70, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 308 | 308 | -1.4721 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 287 | 287 | -0.9449 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 287 | 287 | -0.9449 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 287 | 287 | -0.9449 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 205 | 205 | -1.1965 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 149 | 149 | -1.1954 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 82 | 82 | -0.4947 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 73 | 73 | -1.9439 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 71 | 71 | -0.5373 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 60 | 60 | -1.5474 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 59 | 59 | -0.8543 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 54 | 54 | 0.4099 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 30 | 30 | -1.1625 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 30 | 30 | -1.5223 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 29 | 29 | -2.4349 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 28 | 28 | 0.0837 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 27 | 27 | -0.417 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 27 | 27 | -0.417 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 13064 | 25 | -0.4365 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 0.5397 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 17 | 17 | 0.0789 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.8303 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 14 | 14 | -0.5212 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 11 | 11 | -3.8938 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 11 | 11 | -1.0323 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 2.1642 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.1856 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.3769 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -1.0317 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.4244 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 6 | 6 | 0.16 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 6 | 6 | -3.4922 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 5 | 5 | 1.3504 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 5 | 5 | 0.6518 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
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
- summary: `{'bucket_count': 480, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 14339 | 14180 | None | -1.0792 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 14190 | 14031 | None | -1.0562 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 10400 | 10378 | None | -0.7542 | 0.153 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 7163 | 7145 | None | -1.0184 | 0.0879 | `hold_sample` |
| `ai_score_source` | `live` | 3947 | 3947 | None | -1.0278 | 0.1158 | `hold_sample` |
| `ai_score_band` | `score_70p` | 3510 | 3509 | None | -0.764 | 0.177 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2744 | 2744 | None | -0.7044 | 0.1735 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 2521 | 2479 | None | -0.8974 | 0.0981 | `hold_sample` |
| `qty_reason` | `qty_none` | 2481 | 2479 | None | -0.8974 | 0.0981 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 2523 | 2479 | None | -0.8974 | 0.0981 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2523 | 2479 | None | -0.8974 | 0.0981 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2338 | 2338 | None | -1.1564 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 2364 | 2329 | None | 0.6001 | 0.9836 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2364 | 2329 | None | 0.6001 | 0.9836 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2071 | 2071 | None | -0.9497 | 0.0975 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1905 | 1905 | None | 0.4347 | 0.9816 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1768 | 1765 | None | -0.6279 | 0.1968 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1481 | 1481 | None | -1.4053 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1337 | 1337 | None | -0.6815 | 0.1563 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1262 | 1262 | None | -1.0136 | 0.1046 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 54 | 27 | -0.417 | -0.5559 | 0.1852 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 27 | 27 | -0.417 | -0.5559 | 0.1852 | `hold_sample` |
| `stage` | `exit` | 27 | 27 | -0.417 | -0.5559 | 0.1852 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 54 | 27 | -0.417 | -0.5559 | 0.1852 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 27 | 27 | -0.417 | -0.5559 | 0.1852 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 52 | 26 | -0.3889 | -0.5185 | 0.1923 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 44 | 22 | -0.6027 | -0.8036 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 40 | 20 | -0.5025 | -0.67 | 0.25 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 28 | 14 | -0.2454 | -0.3271 | 0.3571 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 11 | 11 | -0.1732 | -0.2309 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 11 | -1.0323 | -1.3764 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 22 | 11 | -0.1732 | -0.2309 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0207 | -1.361 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 18 | 9 | -0.6742 | -0.8989 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 14 | 7 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
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
