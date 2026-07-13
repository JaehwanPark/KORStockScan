# Lifecycle Decision Matrix - 2026-07-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-13_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `14195`
- source_rows_total: `19875`
- retained_rows: `14195`
- dropped_rows_by_source: `{}`
- joined_rows: `5607`
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
- lifecycle_flow_bucket_count: `195`
- lifecycle_flow_complete_count: `72`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0058`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1672 | 63 | -0.1124 | 0.0626 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 455 | 101 | -0.6028 | 0.5418 | `pass` | `NO_CHANGE` | False |
| `holding` | 285 | 101 | -1.3121 | 0.7563 | `pass` | `EXIT` | False |
| `scale_in` | 5250 | 5127 | -0.8206 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6533 | 215 | -1.0991 | 0.2257 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 195, 'complete_flow_count': 72, 'incomplete_flow_count': 12267, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4480 | 4380 | -1.0498 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 665 | 642 | 0.7632 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 88 | 88 | -1.0511 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 16 | 16 | -0.0942 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -0.7688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 7 | 7 | 0.1809 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 0.652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -1.3575 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.6887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:ad0146c320` | 2 | 2 | -1.8569 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 2 | 2 | -0.5731 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9cad8b8252` | 1 | 1 | -2.0092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:0b49021de5` | 1 | 1 | 1.4487 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9b3d586d84` | 1 | 1 | -1.2667 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:8058890631` | 1 | 1 | -0.7511 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 287, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1000 | 55 | 0.0085 | -0.9446 | 0.3273 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 922 | 47 | 0.1725 | -0.8872 | 0.3404 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1124 | 43 | -0.1903 | -1.4891 | 0.3488 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1135 | 35 | -0.0181 | -1.5394 | 0.2857 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 808 | 31 | 0.0933 | -1.5581 | 0.1936 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 587 | 25 | -0.2691 | -0.4531 | 0.52 | `hold_sample` |
| `score_band` | `score_70p` | 233 | 25 | -0.1623 | -0.7386 | 0.48 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 506 | 25 | -0.0879 | -0.611 | 0.36 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 324 | 22 | -0.0898 | 0.0593 | 0.4545 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 22 | 22 | -0.0617 | -3.5482 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 566 | 22 | -0.241 | -1.4559 | 0.2727 | `hold_sample` |
| `stale_bucket` | `stale_high` | 696 | 21 | -0.1109 | -1.441 | 0.3333 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1629 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 153 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 20 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 334 | 19 | 0.296 | -0.6945 | 0.3684 | `hold_sample` |
| `stale_bucket` | `fresh` | 362 | 16 | -0.2444 | -1.8556 | 0.25 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | -0.3211 | 2.1347 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 377 | 11 | -0.7682 | -2.44 | 0.2727 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 515 | 8 | -0.9438 | -1.2688 | 0.625 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 116, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 344 | 101 | -0.6028 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 446 | 101 | -0.6028 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 272 | 101 | -0.6028 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 272 | 101 | -0.6028 | `keep_collecting` |
| `latency_state` | `simulated` | 272 | 101 | -0.6028 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 344 | 101 | -0.6028 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 269 | 98 | -0.5022 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 257 | 94 | -0.6242 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 237 | 80 | -0.4352 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 162 | 53 | -0.158 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 162 | 53 | -0.158 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 232 | 53 | -0.158 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 162 | 53 | -0.158 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 162 | 53 | -0.158 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 111 | 48 | -1.0941 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 108 | 48 | -1.0941 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 110 | 48 | -1.0941 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 110 | 48 | -1.0941 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 110 | 48 | -1.0941 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 264 | 27 | 0.0256 | `keep_collecting` |
| `would_limit_fill` | `true` | 81 | 26 | -0.3487 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 72 | 25 | -1.3856 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 76 | 23 | 0.1705 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 59 | 21 | -0.8137 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 39 | 21 | -1.178 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 69 | 19 | -0.0983 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 33 | 18 | -0.7999 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 52 | 17 | -0.7135 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 12 | 7 | -1.0282 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 13 | 6 | -0.4506 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | -0.8075 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | -0.8942 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 90 | 2 | -0.3933 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 272 | 101 | -1.3121 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 272 | 101 | -1.3121 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 259 | 96 | -1.3798 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 72 | 68 | -2.1033 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 67 | 67 | -2.0916 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 10 | 9 | 0.2346 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 8 | -0.1975 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | -0.2908 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 7 | 7 | 0.1839 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.0281 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 8 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 13 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 171 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 163 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 145 | 145 | -1.6489 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 113 | 113 | -0.9513 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 113 | 113 | -0.9513 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 113 | 113 | -0.9513 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 89 | 89 | -1.4055 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 79 | 79 | -1.2724 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 47 | 47 | -1.9505 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 38 | 38 | -1.8705 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 34 | 34 | -0.4861 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 31 | 31 | -0.8294 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 29 | 29 | -0.5366 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 25 | 25 | 0.5265 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 23 | 23 | -2.3884 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 20 | 20 | -1.415 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.3178 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 5489 | 13 | -0.2862 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.2862 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.2862 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 11 | 11 | -0.0786 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 10 | 10 | -1.8292 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 9 | 9 | 0.199 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 2.2418 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 7 | 7 | -4.4293 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -1.0317 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.1935 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.9694 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 4 | 4 | -0.1241 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.2567 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -1.3481 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.2672 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.8397 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 412, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 4688 | 4671 | None | -1.0545 | 0.0848 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4578 | 4478 | None | -1.2258 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4505 | 4405 | None | -1.1925 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2810 | 2810 | None | -1.0486 | 0.1306 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1576 | 1576 | None | -0.9017 | 0.111 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1091 | 1091 | None | -1.0852 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 1035 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `qty_reason` | `qty_none` | 997 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1037 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1037 | 995 | None | -0.7463 | 0.1187 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 682 | 661 | None | -0.9392 | 0.0895 | `hold_sample` |
| `arm` | `PYRAMID` | 672 | 649 | None | 0.7398 | 0.986 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 672 | 649 | None | 0.7398 | 0.986 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 536 | 536 | None | -0.9205 | 0.138 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 533 | 533 | None | -1.0561 | 0.0825 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 467 | 467 | None | -1.3686 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 395 | 395 | None | -0.4099 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 392 | 392 | None | 0.4033 | 0.9847 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 354 | 351 | None | -0.0382 | 0.5626 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 287 | 287 | None | -0.6957 | 0.3728 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 26 | 13 | -0.2862 | -0.3815 | 0.2308 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 13 | 13 | -0.2862 | -0.3815 | 0.2308 | `hold_sample` |
| `stage` | `exit` | 13 | 13 | -0.2862 | -0.3815 | 0.2308 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 26 | 13 | -0.2862 | -0.3815 | 0.2308 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 13 | 13 | -0.2862 | -0.3815 | 0.2308 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 24 | 12 | -0.2144 | -0.2858 | 0.25 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.3203 | -0.427 | 0.3 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 20 | 10 | -0.492 | -0.656 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 18 | 9 | -0.325 | -0.4333 | 0.3333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.1737 | -0.2317 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -0.9694 | -1.2925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.91 | -1.2133 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.225 | -0.3 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.96 | 1.28 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_lt_neg070` | 1 | 1 | -1.1475 | -1.53 | 0.0 | `hold_sample` |

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
