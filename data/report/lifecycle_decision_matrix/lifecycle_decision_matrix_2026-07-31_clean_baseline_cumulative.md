# Lifecycle Decision Matrix - 2026-07-31

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-31_clean_baseline_cumulative`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `23242`
- source_rows_total: `48844`
- retained_rows: `23242`
- dropped_rows_by_source: `{}`
- joined_rows: `10380`
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
- lifecycle_flow_bucket_count: `300`
- lifecycle_flow_complete_count: `138`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0072`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4282 | 103 | 0.1148 | 0.1548 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1025 | 147 | -0.4988 | 0.5611 | `pass` | `NO_CHANGE` | False |
| `holding` | 411 | 147 | -1.0995 | 0.7455 | `pass` | `EXIT` | False |
| `scale_in` | 9784 | 9639 | -0.8062 | 0.9994 | `pass` | `NO_CHANGE` | False |
| `exit` | 7740 | 344 | -0.9507 | 0.3519 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 300, 'complete_flow_count': 138, 'incomplete_flow_count': 18979, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8326 | 8209 | -1.0409 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1336 | 1308 | 0.6698 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 96 | 96 | -1.0087 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 19 | 19 | 0.4865 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 16 | 16 | -0.8625 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 11 | 11 | 0.11 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 9 | 9 | -0.3773 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 8 | 8 | 2.8003 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 8 | 8 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 7 | 7 | -0.7971 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 5 | 5 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.236 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 5 | 5 | -0.682 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:35ce26a91c` | 4 | 4 | -1.14 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:964bbee510` | 3 | 3 | -0.8233 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 2 | 2 | -2.7967 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:73753e9274` | 2 | 2 | -1.265 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:97cbb762ac` | 2 | 2 | -2.4121 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 423, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1735 | 86 | 0.3084 | -0.1472 | 0.4535 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1562 | 74 | 0.2174 | -0.2924 | 0.4595 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3090 | 59 | -0.19 | -1.2075 | 0.4068 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2310 | 49 | -0.0626 | -1.3012 | 0.3469 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1392 | 41 | 0.267 | -0.8379 | 0.3659 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1380 | 40 | 0.5705 | 1.2307 | 0.6 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 4216 | 37 | 0.7521 | 1.3132 | 0.5676 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 271 | 37 | 0.7521 | 1.3132 | 0.5676 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1325 | 37 | 0.0217 | -0.1516 | 0.4595 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 37 | 37 | 0.7521 | 1.3132 | 0.5676 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 1094 | 33 | -0.0587 | -1.0182 | 0.4242 | `hold_sample` |
| `score_band` | `score_60_62` | 739 | 30 | -0.2014 | -1.3133 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 849 | 29 | 0.2621 | -0.9809 | 0.3448 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 1891 | 28 | 0.1698 | 0.4388 | 0.5357 | `hold_sample` |
| `score_band` | `score_70p` | 461 | 28 | 0.0857 | 0.1234 | 0.5714 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 27 | 27 | -0.006 | -3.5826 | 0.0 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 369 | 27 | 0.0339 | -0.0216 | 0.5555 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 26 | 26 | -0.5341 | 1.6789 | 0.9615 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 867 | 26 | -0.1742 | -0.2248 | 0.5 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 897 | 19 | -0.2841 | -1.8326 | 0.2632 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 143, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 776 | 147 | -0.4988 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 383 | 147 | -0.4988 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 383 | 147 | -0.4988 | `keep_collecting` |
| `latency_state` | `simulated` | 383 | 147 | -0.4988 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 776 | 147 | -0.4988 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 972 | 146 | -0.4784 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 380 | 144 | -0.4281 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 363 | 138 | -0.5165 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 294 | 99 | -0.4825 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 263 | 96 | -0.249 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 263 | 96 | -0.249 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 259 | 95 | -0.215 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 640 | 95 | -0.215 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 259 | 95 | -0.215 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 123 | 52 | -1.0172 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 124 | 52 | -1.0172 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 120 | 51 | -0.9691 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 120 | 51 | -0.9691 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 120 | 51 | -0.9691 | `keep_collecting` |
| `would_limit_fill` | `true` | 132 | 50 | -0.2399 | `keep_collecting` |
| `would_limit_fill` | `false` | 769 | 45 | -0.1875 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 86 | 45 | -0.3084 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 110 | 35 | -0.0837 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 109 | 28 | -1.4209 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 86 | 26 | -0.3016 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 46 | 24 | -0.173 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 67 | 21 | -0.8961 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 44 | 21 | -1.221 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 51 | 16 | -0.6729 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 10 | -0.5506 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 19 | 8 | -0.3168 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 5 | -0.9485 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 191 | 3 | 1.9036 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 3 | -0.7689 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 383 | 147 | -1.0995 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 383 | 147 | -1.0995 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 371 | 141 | -1.1398 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 96 | 90 | -1.9458 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 88 | 88 | -1.9618 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 22 | 20 | -0.152 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 18 | 18 | -0.2193 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 15 | 13 | -0.0365 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.1033 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 10 | 10 | 1.0621 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 1.0621 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 0.9029 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 0.9029 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 23 | 5 | -0.349 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.349 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.3835 | `hold_sample` |
| `holding_action` | `BUY` | 2 | 2 | -0.1101 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.2424 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.3343 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 28 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 236 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 28 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 230 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 65, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 214 | 214 | -1.4796 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 201 | 201 | -0.8956 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 201 | 201 | -0.8956 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 201 | 201 | -0.8956 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 134 | 134 | -1.2066 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 115 | 115 | -1.2154 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 75 | 75 | -0.4608 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 57 | 57 | -0.5414 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 53 | 53 | -1.8855 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 47 | 47 | -0.8958 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 41 | 41 | -1.6069 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 40 | 40 | 0.3022 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.259 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.259 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 27 | 27 | -1.1772 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 20 | 20 | 0.041 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 6172 | 19 | -0.3 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 19 | 19 | -2.353 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 19 | 19 | -1.5254 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 16 | -0.0831 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -1.7493 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 12 | 12 | -0.8619 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 11 | 11 | 1.7029 | `candidate_recovery_or_relax` |
| `exit_outcome` | `COMPLETED` | 9 | 9 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 9 | 9 | -4.2875 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 9 | 9 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.7428 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.195 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 8 | 8 | -0.8621 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 8 | 8 | -0.4151 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 7 | 7 | 0.1929 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 6 | 6 | -1.015 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 0.5991 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -3.5445 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 5 | 5 | 0.1896 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.3325 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 4 | 4 | 0.1331 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.731 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -5.3572 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 456, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 8437 | 8320 | None | -1.1803 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8290 | 8173 | None | -1.1423 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 6277 | 6260 | None | -1.0261 | 0.0866 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 3739 | 3720 | None | -0.8314 | 0.1732 | `hold_sample` |
| `ai_score_source` | `live` | 3533 | 3533 | None | -1.0728 | 0.1002 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 3553 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `qty_reason` | `qty_none` | 3509 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `time_bucket` | `time_unknown` | 3556 | 3506 | None | -0.8645 | 0.1022 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 3292 | 3242 | None | -0.8503 | 0.1105 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 2865 | 2865 | None | -1.1012 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 2335 | 2334 | None | -0.7923 | 0.2005 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 2171 | 2171 | None | -0.9024 | 0.1156 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 2017 | 2017 | None | -1.3714 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1599 | 1599 | None | -1.0156 | 0.0982 | `hold_sample` |
| `arm` | `PYRAMID` | 1347 | 1319 | None | 0.6266 | 0.9764 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1347 | 1319 | None | 0.6266 | 0.9764 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1249 | 1249 | None | -0.9547 | 0.1033 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1071 | 1071 | None | -0.4239 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1015 | 1015 | None | 0.4107 | 0.9724 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 705 | 705 | None | -0.4541 | 0.4184 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 32, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 56 | 28 | -0.259 | -0.3454 | 0.1429 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 28 | 28 | -0.259 | -0.3454 | 0.1429 | `hold_sample` |
| `stage` | `exit` | 28 | 28 | -0.259 | -0.3454 | 0.1429 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 56 | 28 | -0.259 | -0.3454 | 0.1429 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 28 | 28 | -0.259 | -0.3454 | 0.1429 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 54 | 27 | -0.2261 | -0.3015 | 0.1481 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 48 | 24 | -0.3866 | -0.5154 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 18 | 18 | -0.1771 | -0.2361 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 18 | -0.1975 | -0.2633 | 0.2222 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 36 | 18 | -0.1771 | -0.2361 | 0.0 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 30 | 15 | -0.334 | -0.4453 | 0.2667 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 26 | 13 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 16 | 8 | -0.4191 | -0.5588 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.015 | -1.3533 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 5 | 5 | -0.9885 | -1.318 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |

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
