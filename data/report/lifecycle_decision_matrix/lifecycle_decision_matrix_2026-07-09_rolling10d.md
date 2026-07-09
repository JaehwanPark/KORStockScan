# Lifecycle Decision Matrix - 2026-07-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-09_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `36863`
- source_rows_total: `67424`
- retained_rows: `36863`
- dropped_rows_by_source: `{}`
- joined_rows: `18033`
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
- lifecycle_flow_bucket_count: `259`
- lifecycle_flow_complete_count: `94`
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
| `entry` | 2035 | 144 | 0.9972 | 0.1963 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 827 | 182 | -0.6553 | 0.5951 | `pass` | `NO_CHANGE` | False |
| `holding` | 544 | 182 | -1.174 | 0.7994 | `pass` | `EXIT` | False |
| `scale_in` | 17266 | 17087 | -0.7299 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 16191 | 438 | -1.0185 | 0.1642 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 259, 'complete_flow_count': 94, 'incomplete_flow_count': 34157, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 14298 | 14154 | -0.9841 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2702 | 2667 | 0.6296 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 228 | 228 | -1.0188 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 51 | 51 | 0.9342 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 19 | 19 | 3.1471 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 18 | 18 | 0.1367 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 14 | 14 | 3.2319 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 13 | 13 | -0.9754 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 6 | 6 | -1.215 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.7667 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 5 | 5 | -2.7209 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 5 | 5 | -1.6896 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 2 | 2 | -1.6292 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a4de6797c9` | 16 | 2 | 0.415 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:97cbb762ac` | 2 | 2 | -2.4121 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:de45155b3b` | 2 | 2 | -1.3398 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:df2241cc71` | 2 | 2 | -1.827 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 368, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1217 | 137 | 1.1004 | 1.3336 | 0.5036 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1076 | 110 | 0.5426 | 0.2747 | 0.4818 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 274 | 88 | 1.7614 | 2.9453 | 0.6023 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1975 | 84 | 1.8177 | 3.0351 | 0.5833 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 416 | 84 | 1.8177 | 3.0351 | 0.5833 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 84 | 84 | 1.8177 | 3.0351 | 0.5833 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 425 | 64 | 0.6991 | 0.9675 | 0.5156 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 195 | 63 | 1.7694 | 3.0581 | 0.619 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1132 | 60 | -0.1514 | -1.2487 | 0.4167 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 1028 | 52 | 0.299 | -0.587 | 0.4039 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 589 | 51 | 0.8264 | 0.9315 | 0.451 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1276 | 50 | -0.0362 | -1.4412 | 0.36 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 520 | 46 | 1.1129 | 2.3078 | 0.5652 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 394 | 30 | -0.0058 | -2.1703 | 0.2667 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 30 | 30 | 0.2151 | -3.6243 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 801 | 30 | -0.0143 | -1.2703 | 0.3333 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | -0.4968 | 2.226 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 334 | 25 | 0.5189 | -0.8969 | 0.4 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 318 | 24 | 0.8558 | 0.6422 | 0.4167 | `hold_sample` |
| `stale_bucket` | `stale_high` | 779 | 24 | -0.2098 | -0.5546 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 123, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 558 | 182 | -0.6553 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 520 | 182 | -0.6553 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 520 | 182 | -0.6553 | `keep_collecting` |
| `latency_state` | `simulated` | 520 | 182 | -0.6553 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 558 | 182 | -0.6553 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 819 | 180 | -0.6434 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 517 | 179 | -0.6011 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 476 | 165 | -0.6984 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 399 | 125 | -0.7247 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 336 | 109 | -0.2806 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 336 | 109 | -0.2806 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 329 | 107 | -0.2535 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 364 | 107 | -0.2535 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 329 | 107 | -0.2535 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 190 | 75 | -1.2286 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 191 | 75 | -1.2286 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 186 | 73 | -1.2148 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 184 | 73 | -1.2148 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 184 | 73 | -1.2148 | `keep_collecting` |
| `would_limit_fill` | `true` | 172 | 62 | -0.232 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 119 | 54 | -0.315 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 135 | 49 | -1.4268 | `keep_collecting` |
| `would_limit_fill` | `false` | 464 | 45 | -0.2832 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 91 | 40 | -1.4247 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 118 | 35 | -0.3168 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 132 | 32 | -0.2837 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 54 | 27 | -0.1222 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 62 | 20 | -0.7739 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 49 | 15 | -0.6501 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 40 | 14 | -0.4409 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 25 | 13 | -0.2818 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 7 | -0.5032 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 251 | 6 | -1.1259 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 9 | 4 | -0.7665 | `source_quality_workorder` |
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
| `held_bucket` | `held_not_applicable_at_start` | 520 | 182 | -1.174 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 520 | 182 | -1.174 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 490 | 170 | -1.2614 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 122 | 111 | -2.1475 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 107 | 107 | -2.1571 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 32 | 29 | -0.0518 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 25 | 25 | -0.1386 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 24 | 24 | 0.797 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.6819 | `candidate_recovery_or_relax` |
| `holding_action` | `holding_action_not_applicable_at_start` | 23 | 10 | 0.2717 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 9 | 9 | 0.9143 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 8 | 8 | 0.8347 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 12 | 5 | -0.278 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.278 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 4 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 4 | 4 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 3 | 3 | -2.011 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | 0.7968 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 5 | 2 | -0.9767 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.5266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 24 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 338 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 24 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 320 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 59, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 287 | 287 | -1.5419 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 277 | 277 | -0.9372 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 277 | 277 | -0.9372 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 277 | 277 | -0.9372 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 189 | 189 | -1.2517 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 137 | 137 | -1.2874 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 81 | 81 | -0.4922 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 75 | 75 | -0.5153 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 69 | 69 | -1.9829 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 56 | 56 | -1.7424 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 55 | 55 | -0.8405 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 47 | 47 | 0.4552 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 29 | 29 | -1.5789 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 28 | 28 | 0.1227 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 27 | 27 | -2.4892 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 26 | 26 | -1.2529 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 15777 | 24 | -0.4219 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.4219 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.4219 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 0.5971 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 13 | 13 | -3.8216 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 13 | 13 | -1.8323 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 12 | 1.6982 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 12 | 12 | -0.6555 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 11 | 11 | 0.102 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 11 | 11 | -1.0602 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 9 | 9 | 1.4838 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 7 | 7 | 0.1357 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -3.2583 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.6655 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 6 | 6 | -0.2025 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 6 | 6 | 0.615 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 4 | 4 | 0.0431 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 4 | 4 | 0.5027 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 3 | 3 | 0.86 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.1633 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 3 | 3 | 3.731 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -5.3572 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 439, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 14545 | 14401 | None | -1.0942 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 14341 | 14197 | None | -1.0626 | 0.0 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 13152 | 13136 | None | -0.7693 | 0.1618 | `hold_sample` |
| `ai_score_band` | `score_70p` | 5834 | 5833 | None | -0.776 | 0.186 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 4801 | 4789 | None | -1.0624 | 0.0942 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3153 | 3153 | None | -0.7286 | 0.1729 | `hold_sample` |
| `arm` | `PYRAMID` | 2721 | 2686 | None | 0.5799 | 0.9772 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2721 | 2686 | None | 0.5799 | 0.9772 | `hold_sample` |
| `ai_score_source` | `live` | 2686 | 2686 | None | -1.0717 | 0.1225 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2318 | 2318 | None | 0.4397 | 0.9745 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1890 | 1887 | None | -0.6983 | 0.1709 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1417 | 1417 | None | -0.6881 | 0.1503 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1193 | 1193 | None | -1.0067 | 0.1098 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 571 | 571 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 390 | 390 | None | -0.54 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 345 | 345 | None | -1.586 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 295 | 295 | None | -0.8182 | 0.0712 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.43)` | 222 | 222 | None | -0.43 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 216 | 216 | None | -0.4837 | 0.287 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 204 | 204 | None | -3.2937 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 48 | 24 | -0.4219 | -0.5625 | 0.25 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 24 | 24 | -0.4219 | -0.5625 | 0.25 | `hold_sample` |
| `stage` | `exit` | 24 | 24 | -0.4219 | -0.5625 | 0.25 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 48 | 24 | -0.4219 | -0.5625 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 24 | 24 | -0.4219 | -0.5625 | 0.25 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 46 | 23 | -0.3903 | -0.5204 | 0.2609 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 46 | 23 | -0.4327 | -0.577 | 0.2609 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 36 | 18 | -0.7196 | -0.9594 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 30 | 15 | -0.179 | -0.2387 | 0.4 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 11 | -1.0602 | -1.4136 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -1.0515 | -1.402 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 7 | 7 | -0.1843 | -0.2457 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 14 | 7 | -0.1843 | -0.2457 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.9762 | -1.3016 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 3 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.86 | 1.1467 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.86 | 1.1467 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 3 | 0.0825 | 0.11 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 6 | 3 | 0.86 | 1.1467 | 1.0 | `hold_sample` |

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
