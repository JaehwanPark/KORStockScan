# Lifecycle Decision Matrix - 2026-07-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-03_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `51910`
- source_rows_total: `85416`
- retained_rows: `51910`
- dropped_rows_by_source: `{}`
- joined_rows: `29415`
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
- lifecycle_flow_bucket_count: `310`
- lifecycle_flow_complete_count: `157`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0033`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3704 | 423 | 0.9307 | 0.7565 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 875 | 334 | -0.6356 | 0.8764 | `pass` | `NO_CHANGE` | False |
| `holding` | 667 | 334 | -1.0247 | 0.9327 | `pass` | `EXIT` | False |
| `scale_in` | 28036 | 27604 | -0.5895 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 18628 | 720 | -0.9373 | 0.5742 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 310, 'complete_flow_count': 157, 'incomplete_flow_count': 47495, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 22127 | 21969 | -0.9037 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5511 | 5237 | 0.7449 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 343 | 343 | -0.9821 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 136 | 136 | 0.92 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 104 | 104 | 2.2154 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 34 | 34 | 2.8451 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 26 | 26 | -0.2591 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -0.6341 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 7 | 7 | -0.7929 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 5 | 5 | -0.8422 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 4 | 4 | -2.1825 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 3 | 3 | -1.2664 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 3 | 3 | -1.0287 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2a4bfd22da` | 3 | 3 | -1.3519 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:4874ec99fd` | 3 | 3 | -2.057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:224eb1ba18` | 3 | 3 | -2.1539 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 3 | 3 | -0.8367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 3 | 3 | -0.7667 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3ba076b12f` | 2 | 2 | -1.2344 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 430, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2726 | 418 | 0.9513 | 1.3454 | 0.4737 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2313 | 315 | 0.758 | 0.8919 | 0.4698 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 373 | 278 | 1.6291 | 2.6633 | 0.5899 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3555 | 274 | 1.6505 | 2.6991 | 0.5876 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 202 | 202 | 1.8986 | 3.0721 | 0.6138 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 2682 | 135 | -0.4131 | -1.2148 | 0.2592 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1747 | 134 | -0.4702 | -1.2963 | 0.2463 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 465 | 125 | 2.0481 | 3.3237 | 0.64 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 374 | 117 | 1.5218 | 2.5258 | 0.5726 | `hold_sample` |
| `score_band` | `score_70p` | 484 | 108 | 0.66 | 0.8277 | 0.4815 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1120 | 89 | 0.233 | -0.5121 | 0.3258 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 1484 | 85 | -0.5101 | -1.3573 | 0.2118 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 200 | 84 | 2.4201 | 4.1383 | 0.6666 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 73 | 73 | -0.1752 | -2.2923 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 554 | 73 | 1.3985 | 1.8721 | 0.5343 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 517 | 69 | 1.0104 | 2.4537 | 0.5797 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_watch` | 550 | 63 | 0.4355 | 0.5562 | 0.4286 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 565 | 55 | -0.0972 | -1.4486 | 0.2 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 913 | 50 | -0.6906 | -1.0354 | 0.28 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 520 | 49 | -0.2899 | -1.9476 | 0.1633 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 272 | 47 | 1.918 | 3.0862 | 0.5958 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

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
| `actual_order_submitted` | `false` | 674 | 334 | -0.6356 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 638 | 334 | -0.6356 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 638 | 334 | -0.6356 | `keep_collecting` |
| `latency_state` | `simulated` | 638 | 334 | -0.6356 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 674 | 334 | -0.6356 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 635 | 333 | -0.6238 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 593 | 313 | -0.6577 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 518 | 267 | -0.6799 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 406 | 249 | -0.7274 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 421 | 216 | -0.4808 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 421 | 216 | -0.4808 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 314 | 215 | -0.6592 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 288 | 207 | -0.6429 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 294 | 186 | -0.7661 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 187 | 130 | -0.5237 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 227 | 118 | -0.919 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 217 | 118 | -0.919 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 217 | 118 | -0.919 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 554 | 117 | -0.5736 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 125 | 90 | -0.3856 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 232 | 85 | -0.3668 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 246 | 85 | -0.3668 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 232 | 85 | -0.3668 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 123 | 66 | -0.3965 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 81 | 60 | -1.0204 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 110 | 45 | -0.1968 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 117 | 42 | -1.1441 | `keep_collecting` |
| `would_limit_fill` | `false` | 359 | 40 | -0.5581 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 74 | 37 | -0.7587 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 97 | 26 | -0.6375 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 232 | 25 | -0.5 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 45 | 23 | 0.0069 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 65 | 22 | -0.4099 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 21 | -1.4311 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 40 | 16 | -0.5918 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 638 | 334 | -1.0247 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 638 | 334 | -1.0247 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 596 | 309 | -1.0622 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 241 | 226 | -1.6953 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 209 | 209 | -1.6957 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 38 | 34 | -0.0816 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 32 | 32 | 0.8949 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 32 | 32 | -0.1223 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 29 | 29 | 0.8216 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 26 | 18 | -0.6056 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 19 | 18 | 1.7284 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 18 | 18 | -0.6056 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 32 | 17 | -0.5526 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 15 | 15 | 1.4902 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.5828 | `hold_sample` |
| `holding_action` | `BUY` | 10 | 8 | -0.5793 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 6 | -0.8635 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -1.8872 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.8635 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 29 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 17 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 304 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 29 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 287 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 64, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 501 | 501 | -1.3645 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 402 | 402 | -0.9132 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 402 | 402 | -0.9132 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 402 | 402 | -0.9132 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 289 | 289 | -1.0383 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 284 | 284 | -1.1625 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 131 | 131 | -1.4358 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 121 | 121 | -1.5808 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 118 | 118 | -0.5455 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 101 | 101 | -0.5383 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 92 | 92 | -0.5679 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 76 | 76 | -0.7439 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 72 | 72 | -2.1018 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 63 | 63 | 0.7517 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 57 | 57 | -1.8865 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 42 | 42 | -1.0687 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 37 | 37 | 0.1513 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 31 | 31 | -1.1508 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 30 | 30 | 0.9525 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 17937 | 29 | -0.2635 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 29 | 29 | -0.2635 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 29 | 29 | -0.2635 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 29 | 29 | -2.8649 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 29 | 29 | -1.5268 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 21 | 21 | 2.0638 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 19 | 19 | -0.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 15 | 15 | -0.934 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 14 | 14 | -1.7122 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 13 | 13 | -0.3357 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 11 | 11 | -1.2309 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 10 | 10 | 0.3187 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 10 | 10 | 0.93 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 10 | 10 | 1.9713 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 8 | 8 | -0.2175 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 7 | 7 | 0.1171 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 7 | 7 | 1.0214 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 7 | 7 | 0.9926 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 5 | 5 | 0.357 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 5 | 5 | 0.8472 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 649, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 27291 | 27290 | None | -0.6497 | 0.1842 | `hold_sample` |
| `arm` | `AVG_DOWN` | 22496 | 22338 | None | -0.9696 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 20153 | 19995 | None | -1.0115 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 14178 | 14178 | None | -0.6042 | 0.2148 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 6661 | 6661 | None | -0.6946 | 0.1632 | `hold_sample` |
| `arm` | `PYRAMID` | 5540 | 5266 | None | 0.6935 | 0.9584 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 5540 | 5266 | None | 0.6935 | 0.9584 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 4551 | 4551 | None | 0.4924 | 0.9732 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2952 | 2952 | None | -0.7342 | 0.1145 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2343 | 2343 | None | -0.6122 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2134 | 2134 | None | -0.6868 | 0.1439 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1668 | 1667 | None | -0.7155 | 0.156 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 691 | 691 | None | -0.6803 | 0.0391 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 510 | 510 | None | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 431 | 431 | None | -0.819 | 0.065 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 398 | 398 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `low_broken` | 345 | 345 | None | -0.6028 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 58 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 29 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 58 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `stage` | `exit` | 29 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 58 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 29 | 29 | -0.2635 | -0.3514 | 0.2069 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 56 | 28 | -0.2668 | -0.3557 | 0.2143 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 46 | 23 | -0.6848 | -0.913 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 34 | 17 | 0.1451 | 0.1935 | 0.3529 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 15 | 15 | -0.934 | -1.2453 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 30 | 15 | -0.934 | -1.2453 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.2175 | -0.29 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2175 | -0.29 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -1.194 | -1.592 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.8137 | 1.085 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 8 | 4 | -0.6131 | -0.8175 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.8137 | 1.085 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.8137 | 1.085 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 6 | 3 | -0.5625 | -0.75 | 0.0 | `hold_sample` |
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
