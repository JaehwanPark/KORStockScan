# Lifecycle Decision Matrix - 2026-07-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-10_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `13592`
- source_rows_total: `18702`
- retained_rows: `13592`
- dropped_rows_by_source: `{}`
- joined_rows: `5258`
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
- lifecycle_flow_bucket_count: `180`
- lifecycle_flow_complete_count: `63`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0053`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1490 | 56 | -0.0411 | 0.067 | `pass` | `NO_CHANGE` | False |
| `submit` | 412 | 92 | -0.6081 | 0.5764 | `pass` | `NO_CHANGE` | False |
| `holding` | 269 | 92 | -1.2914 | 0.7808 | `pass` | `EXIT` | False |
| `scale_in` | 4948 | 4826 | -0.807 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6473 | 192 | -1.0897 | 0.1471 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 180, 'complete_flow_count': 63, 'incomplete_flow_count': 11853, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 4199 | 4100 | -1.0475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 657 | 634 | 0.7641 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 75 | 75 | -1.0572 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 16 | 16 | -0.0942 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -0.7688 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 7 | 7 | 0.1809 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 0.652 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 4 | 4 | -1.3575 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:15c17a2405` | 3 | 3 | -2.6964 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b4078edac9` | 3 | 3 | -2.6887 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.6967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bb8a19e627` | 2 | 2 | -0.5731 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:10cd1f01cf` | 2 | 2 | -2.2218 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 2 | 2 | -1.1385 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 2 | 2 | -1.07 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9cad8b8252` | 1 | 1 | -2.0092 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:0b49021de5` | 1 | 1 | 1.4487 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:9b3d586d84` | 1 | 1 | -1.2667 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:50ebb4b990` | 1 | 1 | -1.45 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:3ecc9eeb81` | 1 | 1 | 0.9467 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 279, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 945 | 52 | 0.0121 | -0.8082 | 0.3461 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 866 | 45 | 0.1691 | -0.8176 | 0.3555 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 981 | 36 | -0.0944 | -1.3517 | 0.3611 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1054 | 32 | -0.0147 | -1.3735 | 0.3125 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 759 | 26 | 0.1556 | -1.2135 | 0.2308 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 498 | 23 | -0.1346 | -0.5525 | 0.4783 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 463 | 23 | -0.1194 | -0.3776 | 0.3913 | `hold_sample` |
| `score_band` | `score_70p` | 207 | 22 | -0.0334 | -0.5338 | 0.5 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 241 | 20 | 0.0882 | 0.2252 | 0.45 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1454 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 139 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `score_band` | `score_60_62` | 555 | 20 | -0.2505 | -1.2585 | 0.3 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 20 | 20 | 0.055 | 0.0963 | 0.4 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 19 | 19 | -0.0261 | -3.5879 | 0.0 | `hold_sample` |
| `stale_bucket` | `stale_high` | 638 | 17 | 0.0096 | -1.2018 | 0.3529 | `hold_sample` |
| `stale_bucket` | `fresh` | 347 | 16 | -0.2444 | -1.8556 | 0.25 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 309 | 16 | 0.451 | -0.4759 | 0.375 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 13 | 13 | -0.0912 | 2.3569 | 1.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 346 | 9 | -0.5234 | -2.6267 | 0.2222 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 8 | 8 | -0.2911 | -0.4169 | 0.5 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 114, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 305 | 92 | -0.6081 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 405 | 92 | -0.6081 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 257 | 92 | -0.6081 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 257 | 92 | -0.6081 | `keep_collecting` |
| `latency_state` | `simulated` | 257 | 92 | -0.6081 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 305 | 92 | -0.6081 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 254 | 89 | -0.4974 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 243 | 86 | -0.6399 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 225 | 74 | -0.4718 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 106 | 46 | -1.1382 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 104 | 46 | -1.1382 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 152 | 46 | -0.078 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 152 | 46 | -0.078 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 198 | 46 | -0.078 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 152 | 46 | -0.078 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 105 | 46 | -1.1382 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 105 | 46 | -1.1382 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 105 | 46 | -1.1382 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 152 | 46 | -0.078 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 70 | 24 | -1.4588 | `keep_collecting` |
| `would_limit_fill` | `false` | 229 | 23 | 0.0936 | `keep_collecting` |
| `would_limit_fill` | `true` | 78 | 23 | -0.2496 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 55 | 20 | -0.8281 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 70 | 20 | 0.2041 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 38 | 20 | -1.2554 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 68 | 18 | -0.1269 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 16 | -0.7252 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 30 | 15 | -0.6239 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 12 | 5 | -0.2806 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 10 | 5 | -0.6915 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 3 | 3 | -3.8922 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.6432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 3 | -0.8942 | `source_quality_workorder` |
| `overbought_guard_action` | `would_block` | 3 | 3 | -3.8922 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 87 | 2 | -0.3933 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 257 | 92 | -1.2914 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 257 | 92 | -1.2914 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 244 | 87 | -1.365 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 65 | 61 | -2.1393 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 60 | 60 | -2.1268 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 9 | 8 | 0.2698 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 9 | 7 | -0.0646 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 6 | 1.6858 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.1513 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | 0.2224 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.7127 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 7 | 3 | -0.0281 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 7 | 2 | -0.3 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.3 | `hold_sample` |
| `holding_action` | `BUY` | 3 | 1 | -0.4267 | `hold_sample` |
| `holding_action` | `DROP` | 3 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.4267 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.4555 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -2.886 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2504 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.5514 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 165 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=DROP|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 157 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 63, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 130 | 130 | -1.6662 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 100 | 100 | -0.9428 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 80 | 80 | -1.3923 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 71 | 71 | -1.2755 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 42 | 42 | -1.9713 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 34 | 34 | -1.9176 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 30 | 30 | -0.7605 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 28 | 28 | -0.4681 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 24 | 24 | -0.5129 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 23 | 23 | 0.6234 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 20 | 20 | -2.455 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 16 | 16 | -1.4608 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 14 | 14 | -1.3178 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 5488 | 12 | -0.2957 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.2957 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.2957 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | 0.0263 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 8 | 0.2298 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 8 | 8 | 0.0575 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 8 | 8 | 2.2418 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 8 | 8 | -1.9054 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 7 | 7 | -4.4293 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.7144 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 4 | 4 | -0.9694 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.1988 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 1.302 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 4 | 4 | 1.0808 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 3 | 3 | -2.7856 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 3 | 3 | 0.055 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.2567 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -4.0827 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.1496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 3 | 3 | 0.2672 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 2 | 2 | 3.9095 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -5.5389 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -3.8397 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 2 | 2 | -0.9288 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.5731 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 398, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 4391 | 4374 | None | -1.0396 | 0.0892 | `hold_sample` |
| `arm` | `AVG_DOWN` | 4284 | 4185 | None | -1.22 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4218 | 4119 | None | -1.1877 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 2638 | 2638 | None | -1.0255 | 0.138 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1504 | 1504 | None | -0.8925 | 0.1164 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 918 | 918 | None | -1.0505 | 0.0 | `hold_sample` |
| `price_guard_reason` | `price_guard_none` | 733 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `qty_reason` | `qty_none` | 696 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 735 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `time_bucket` | `time_unknown` | 735 | 694 | None | -0.5258 | 0.1587 | `hold_sample` |
| `arm` | `PYRAMID` | 664 | 641 | None | 0.7405 | 0.9858 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 664 | 641 | None | 0.7405 | 0.9858 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 627 | 606 | None | -0.9339 | 0.0894 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 432 | 432 | None | -1.0188 | 0.0995 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 428 | 428 | None | -0.8202 | 0.1635 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 390 | 390 | None | 0.405 | 0.9846 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 352 | 349 | None | -0.0375 | 0.5629 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 314 | 314 | None | -0.3914 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 258 | 258 | None | -1.1438 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 222 | 222 | None | -0.7698 | 0.1216 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 24 | 12 | -0.2957 | -0.3942 | 0.25 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 12 | 12 | -0.2957 | -0.3942 | 0.25 | `hold_sample` |
| `stage` | `exit` | 12 | 12 | -0.2957 | -0.3942 | 0.25 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 24 | 12 | -0.2957 | -0.3942 | 0.25 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.2957 | -0.3942 | 0.25 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 22 | 11 | -0.2182 | -0.2909 | 0.2727 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 20 | 10 | -0.3203 | -0.427 | 0.3 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 18 | 9 | -0.5275 | -0.7033 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 16 | 8 | -0.3441 | -0.4587 | 0.375 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 10 | 5 | -0.174 | -0.232 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 4 | -0.9694 | -1.2925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 3 | 3 | -0.91 | -1.2133 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 2 | 2 | 0.12 | 0.16 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
