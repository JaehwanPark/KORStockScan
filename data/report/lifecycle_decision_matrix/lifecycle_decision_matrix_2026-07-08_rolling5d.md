# Lifecycle Decision Matrix - 2026-07-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-08_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `10726`
- source_rows_total: `14802`
- retained_rows: `10726`
- dropped_rows_by_source: `{}`
- joined_rows: `3993`
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
- lifecycle_flow_bucket_count: `140`
- lifecycle_flow_complete_count: `47`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0049`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 875 | 44 | -0.0572 | 0.0817 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 289 | 72 | -0.6248 | 0.6626 | `pass` | `NO_CHANGE` | False |
| `holding` | 206 | 72 | -1.3868 | 0.8583 | `pass` | `EXIT` | False |
| `scale_in` | 3722 | 3647 | -0.8281 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5634 | 158 | -1.1254 | 0.1577 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 140, 'complete_flow_count': 47, 'incomplete_flow_count': 9599, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 3145 | 3085 | -1.083 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 498 | 483 | 0.8101 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 66 | 66 | -1.0489 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 13 | 13 | -0.2283 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -0.7688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 5 | 5 | 0.3352 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 0.652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.6887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 2 | 2 | -2.5496 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 2 | 2 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9cad8b8252` | 1 | 1 | -2.0092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:50ebb4b990` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:d284f9c76b` | 1 | 1 | -0.7822 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:05b5bc258b` | 1 | 1 | -0.37 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:494385f683` | 1 | 1 | 0.24 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9f155f5933` | 1 | 1 | -2.6744 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 225, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 617 | 43 | -0.0604 | -1.0991 | 0.2558 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 550 | 37 | 0.1479 | -1.24 | 0.2432 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 528 | 27 | -0.0799 | -1.7315 | 0.2592 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 659 | 26 | -0.0859 | -1.8373 | 0.2308 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 544 | 23 | 0.0077 | -1.2057 | 0.2174 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 18 | 18 | -0.088 | -3.5733 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 64 | 17 | 0.0765 | 0.2298 | 0.3529 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 848 | 17 | -0.0212 | 0.0298 | 0.2941 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 125 | 17 | -0.0212 | 0.0298 | 0.2941 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 185 | 17 | 0.0177 | -0.7297 | 0.3529 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 269 | 17 | -0.1253 | -1.0679 | 0.1765 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 17 | 17 | -0.0212 | 0.0298 | 0.2941 | `hold_sample` |
| `score_band` | `score_70p` | 83 | 16 | 0.0506 | -0.4645 | 0.375 | `hold_sample` |
| `score_band` | `score_60_62` | 360 | 15 | -0.2945 | -1.824 | 0.2 | `hold_sample` |
| `stale_bucket` | `fresh` | 171 | 14 | -0.2594 | -2.1629 | 0.2143 | `hold_sample` |
| `stale_bucket` | `stale_high` | 433 | 12 | 0.1163 | -1.4575 | 0.25 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 128 | 12 | 0.2409 | -0.3179 | 0.3333 | `hold_sample` |
| `time_bucket` | `time_1400_close` | 259 | 8 | -0.2573 | -0.8491 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 7 | 7 | -0.2438 | 2.99 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 219 | 7 | -0.1743 | -2.4972 | 0.1429 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 96, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 209 | 72 | -0.6248 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 289 | 72 | -0.6248 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 197 | 72 | -0.6248 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 197 | 72 | -0.6248 | `keep_collecting` |
| `latency_state` | `simulated` | 197 | 72 | -0.6248 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 209 | 72 | -0.6248 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 195 | 70 | -0.4881 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 186 | 68 | -0.6514 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 170 | 58 | -0.5442 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 85 | 36 | -1.2062 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 83 | 36 | -1.2062 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 113 | 36 | -0.0434 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 113 | 36 | -0.0434 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 124 | 36 | -0.0434 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 113 | 36 | -0.0434 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 84 | 36 | -1.2062 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 84 | 36 | -1.2062 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 84 | 36 | -1.2062 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 113 | 36 | -0.0434 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 54 | 20 | -1.735 | `keep_collecting` |
| `would_limit_fill` | `true` | 63 | 20 | -0.0732 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 55 | 17 | -0.1217 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 17 | -1.5092 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 142 | 16 | -0.006 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 39 | 14 | -0.5668 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 46 | 13 | 0.141 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 26 | 12 | -0.217 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 34 | 11 | -0.5154 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 10 | 4 | -0.1722 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.6432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 3 | 0.2015 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 2 | 2 | -5.409 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 71 | 2 | -0.3933 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | 0.0045 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | -0.3933 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 197 | 72 | -1.3868 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 197 | 72 | -1.3868 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 185 | 68 | -1.4608 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 52 | 50 | -2.1259 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 49 | 49 | -2.1104 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 8 | 7 | 0.2776 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.4724 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 6 | 6 | -0.4724 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 5 | 5 | 0.2239 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 4 | 4 | 1.9299 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.0281 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 5 | 3 | 0.0733 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.0733 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.0561 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `DROP` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 9 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 6 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 125 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 117 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
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
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 111 | 111 | -1.6382 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 87 | 87 | -0.9343 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 87 | 87 | -0.9343 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 87 | 87 | -0.9343 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 63 | 63 | -1.2581 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 62 | 62 | -1.5376 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 36 | 36 | -1.9587 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 29 | 29 | -2.158 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 23 | 23 | -0.4714 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 20 | 20 | -0.8017 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 20 | 20 | -0.511 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 18 | 18 | -2.4562 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | 0.6504 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 13 | 13 | -1.2856 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 11 | 11 | -1.2165 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 5485 | 9 | -0.1325 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.1325 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.1325 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 7 | 7 | 0.2319 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -1.846 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 6 | 6 | -0.4724 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 2.5898 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 5 | 5 | 0.109 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 5 | 5 | -4.5185 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.7436 | `candidate_tighten_or_exclude` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 3 | 3 | -0.2075 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.8475 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 2 | 2 | 0.19 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -4.3141 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 2 | 2 | 1.4063 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 0.2934 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 2 | 2 | 0.5145 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 2 | 2 | 2.4535 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 2 | 2 | -0.1527 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 324, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 3309 | 3299 | None | -1.0818 | 0.0864 | `hold_sample` |
| `arm` | `AVG_DOWN` | 3219 | 3159 | None | -1.2612 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 3164 | 3104 | None | -1.2261 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2024 | 2024 | None | -1.0197 | 0.1452 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1130 | 1130 | None | -0.9803 | 0.1142 | `hold_sample` |
| `arm` | `PYRAMID` | 503 | 488 | None | 0.7829 | 0.9876 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 503 | 488 | None | 0.7829 | 0.9876 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 449 | 435 | None | -0.9485 | 0.0647 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 296 | 296 | None | 0.3951 | 0.9831 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 291 | 288 | None | 0.0127 | 0.5849 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 96 | 96 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 91 | 91 | None | -0.4923 | 0.2857 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 90 | 90 | None | -0.946 | 0.0667 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.70)` | 60 | 60 | None | -0.7 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.08)` | 59 | 59 | None | -1.08 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 55 | 55 | None | -3.2458 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 51 | 51 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.64)` | 44 | 44 | None | -0.64 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.69)` | 44 | 44 | None | -1.69 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.59)` | 42 | 42 | None | -0.59 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 18 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 9 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 18 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `stage` | `exit` | 9 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 18 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 9 | 9 | -0.1325 | -0.1767 | 0.3333 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 16 | 8 | -0.1275 | -0.17 | 0.375 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 12 | 6 | -0.095 | -0.1267 | 0.5 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 12 | 6 | -0.3988 | -0.5317 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1744 | -0.2325 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1744 | -0.2325 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 2 | -0.8475 | -1.13 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |

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
