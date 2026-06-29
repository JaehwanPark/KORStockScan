# Lifecycle Decision Matrix - 2026-06-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-29_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `39757`
- source_rows_total: `50030`
- retained_rows: `39757`
- dropped_rows_by_source: `{}`
- joined_rows: `24173`
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
- lifecycle_flow_bucket_count: `305`
- lifecycle_flow_complete_count: `241`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0069`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4049 | 473 | 0.655 | 0.8588 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 814 | 494 | -0.5236 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 787 | 494 | -1.0751 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 22284 | 21723 | -0.489 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 11823 | 989 | -0.9285 | 0.9025 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 305, 'complete_flow_count': 241, 'incomplete_flow_count': 34566, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 16792 | 16652 | -0.8634 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5014 | 4593 | 0.8975 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 383 | 383 | -0.9794 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 146 | 146 | 1.0352 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 101 | 101 | 1.6319 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 46 | 46 | -0.0056 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 24 | 24 | 3.0114 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 14 | 14 | -0.8125 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 8 | 8 | -1.025 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.349 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 6 | 6 | -1.8851 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.6133 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 6 | 6 | -0.7393 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 5 | 5 | -1.5047 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 4 | 4 | -1.8461 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -1.0246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -1.5619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 3 | 3 | 2.7581 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 390, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3116 | 471 | 0.663 | 0.7068 | 0.414 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2692 | 354 | 0.7026 | 0.4851 | 0.4039 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 273 | 273 | 1.4131 | 2.2557 | 0.5714 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3849 | 273 | 1.4131 | 2.2557 | 0.5714 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 201 | 201 | 1.5773 | 2.4716 | 0.592 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1954 | 185 | -0.4347 | -1.5438 | 0.173 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 3109 | 179 | -0.4143 | -1.4164 | 0.2123 | `hold_no_edge` |
| `score_band` | `score_70p` | 406 | 133 | 0.6754 | 0.7738 | 0.4587 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 428 | 133 | 0.9449 | 1.3297 | 0.5113 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1011 | 129 | 0.1013 | -0.475 | 0.3178 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 1474 | 125 | 0.1243 | -0.8424 | 0.224 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 536 | 124 | 1.5286 | 2.3524 | 0.6048 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1841 | 112 | -0.541 | -1.709 | 0.1518 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 100 | 100 | -0.2817 | -2.0511 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 657 | 90 | 0.062 | 0.5791 | 0.4444 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 719 | 89 | 1.1645 | 1.2266 | 0.4382 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 183 | 82 | 1.705 | 2.6772 | 0.5854 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_high` | 1146 | 82 | -0.5993 | -1.8278 | 0.1463 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 687 | 73 | -0.2871 | -1.4622 | 0.1781 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 54 | 54 | -0.2915 | -3.418 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 47 | 47 | 1.0995 | 1.5911 | 0.5319 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 38 | 38 | 0.865 | 1.0218 | 0.6316 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 130, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 787 | 494 | -0.5236 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 743 | 494 | -0.5236 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 743 | 494 | -0.5236 | `keep_collecting` |
| `latency_state` | `simulated` | 743 | 494 | -0.5236 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 787 | 494 | -0.5236 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 737 | 491 | -0.5169 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 714 | 475 | -0.5289 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 715 | 467 | -0.5388 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 674 | 445 | -0.5603 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 636 | 408 | -0.5624 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 617 | 408 | -0.5643 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 535 | 363 | -0.5325 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 403 | 247 | -0.4145 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 403 | 247 | -0.4145 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 356 | 244 | -0.6363 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 337 | 244 | -0.6363 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 337 | 244 | -0.6363 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 370 | 226 | -0.4005 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 264 | 158 | -0.2848 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 212 | 157 | -0.8391 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 107 | 83 | -0.2932 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 133 | 77 | -0.6554 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 94 | 66 | -0.3265 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 59 | 41 | -0.2262 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 33 | -0.96 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 84 | 31 | -0.2713 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 99 | 27 | -0.2609 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 29 | 25 | -0.1862 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 47 | 22 | -0.3832 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 40 | 20 | -0.7836 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 29 | 19 | -0.391 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 29 | 19 | -0.391 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 19 | -0.4655 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 16 | -0.6605 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 94 | 14 | -0.5306 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 742 | 494 | -1.0751 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 742 | 494 | -1.0751 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 638 | 419 | -1.0704 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 391 | 377 | -1.5684 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 314 | 314 | -1.5638 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 90 | 63 | -1.1148 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 53 | 53 | -1.5312 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 36 | 33 | 0.7291 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 31 | 31 | 0.6637 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 32 | 26 | 0.2069 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 26 | 26 | 0.2069 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 25 | 23 | 2.1045 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 36 | 22 | -0.5982 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 20 | 20 | -0.6155 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 16 | 16 | 2.1223 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 19 | 13 | -0.3482 | `hold_no_edge` |
| `holding_action` | `BUY` | 14 | 12 | -1.033 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.4214 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -1.9085 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.5512 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 45 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 33 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 248 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 45 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 219 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 66, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 721 | 721 | -1.3633 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 475 | 475 | -0.8458 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 475 | 475 | -0.8458 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 475 | 475 | -0.8458 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 469 | 469 | -1.1087 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 332 | 332 | -1.1539 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 207 | 207 | -1.2697 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 198 | 198 | -1.6629 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 169 | 169 | -1.9151 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 154 | 154 | -0.4564 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 128 | 128 | -0.5115 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 117 | 117 | -1.0292 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 106 | 106 | -0.5057 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 99 | 99 | -1.752 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 70 | 70 | 1.0603 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 69 | 69 | -1.3566 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 61 | 61 | -2.6536 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 57 | 57 | -0.6285 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 50 | 50 | -1.0711 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 10879 | 45 | 0.0773 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 45 | 45 | 0.0773 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 45 | 45 | 0.0773 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 39 | 39 | 0.9253 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.7482 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 35 | 35 | -0.0023 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 35 | 35 | 0.3618 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 31 | 31 | 2.6293 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 22 | 22 | 0.2209 | `hold_no_edge` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 19 | 19 | -0.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 14 | 14 | -0.9563 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 14 | 14 | 0.1194 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 13 | 13 | -0.2775 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 12 | 12 | 1.8893 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 11 | 11 | 1.1738 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 10 | 10 | 3.0919 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 9 | 9 | 0.9844 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 8 | 8 | -1.0275 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 6 | 6 | 0.7875 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 636, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 21707 | 21707 | None | -0.5408 | 0.2054 | `hold_sample` |
| `arm` | `AVG_DOWN` | 17215 | 17075 | None | -0.9188 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 13439 | 13299 | None | -1.0606 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 12093 | 12093 | None | -0.4983 | 0.2381 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4819 | 4819 | None | -0.6252 | 0.1666 | `hold_sample` |
| `arm` | `PYRAMID` | 5069 | 4648 | None | 0.8506 | 0.9616 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 5069 | 4648 | None | 0.8506 | 0.9616 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3776 | 3776 | None | -0.4197 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 3704 | 3704 | None | 0.538 | 0.9798 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2433 | 2433 | None | -0.5862 | 0.1615 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1279 | 1279 | None | -0.5702 | 0.1564 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1083 | 1083 | None | -0.504 | 0.1708 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 889 | 889 | None | -0.4861 | 0.0652 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 564 | 564 | None | -0.8563 | 0.1099 | `hold_sample` |
| `blocker_reason` | `low_broken` | 487 | 487 | None | -0.4165 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 432 | 432 | None | 3.1409 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 367 | 367 | None | -0.4359 | 0.0845 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 38, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 90 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 45 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 90 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 45 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 90 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 45 | 45 | 0.0773 | 0.1031 | 0.3556 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 84 | 42 | 0.0951 | 0.1269 | 0.3809 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 66 | 33 | 0.2286 | 0.3049 | 0.3939 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 58 | 29 | -0.5904 | -0.7872 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 14 | 14 | -0.9563 | -1.275 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 14 | 14 | -0.263 | -0.3507 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 28 | 14 | -0.9563 | -1.275 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 28 | 14 | -0.263 | -0.3507 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 6 | 6 | 0.7875 | 1.05 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.1937 | -0.2583 | 0.5 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 12 | 6 | 0.7875 | 1.05 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 12 | 6 | 0.7875 | 1.05 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.2745 | 0.366 | 1.0 | `hold_sample` |

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
