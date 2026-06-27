# Lifecycle Decision Matrix - 2026-06-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-26_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `31965`
- source_rows_total: `39885`
- retained_rows: `31965`
- dropped_rows_by_source: `{}`
- joined_rows: `20108`
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
- lifecycle_flow_bucket_count: `277`
- lifecycle_flow_complete_count: `222`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.008`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3249 | 386 | 0.6131 | 0.8391 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 751 | 462 | -0.5708 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 734 | 462 | -1.1331 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 18388 | 17860 | -0.3909 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 8843 | 938 | -0.9523 | 0.9468 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 277, 'complete_flow_count': 222, 'incomplete_flow_count': 27453, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 13262 | 13144 | -0.8004 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 4669 | 4259 | 0.9137 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 370 | 370 | -0.9707 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 99 | 99 | 1.0222 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 78 | 78 | 1.8022 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 43 | 43 | 0.007 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 22 | 22 | 3.5336 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 13 | 13 | -0.8158 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.349 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 7 | 7 | -1.08 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'bucket_count': 337, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2418 | 384 | 0.6227 | 0.5597 | 0.3906 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2149 | 293 | 0.6496 | 0.293 | 0.372 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 201 | 201 | 1.5773 | 2.4716 | 0.592 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3064 | 201 | 1.5773 | 2.4716 | 0.592 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 201 | 201 | 1.5773 | 2.4716 | 0.592 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1954 | 185 | -0.4347 | -1.5438 | 0.173 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 2438 | 164 | -0.4794 | -1.5399 | 0.1829 | `hold_no_edge` |
| `score_band` | `score_70p` | 406 | 133 | 0.6754 | 0.7738 | 0.4587 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 428 | 133 | 0.9449 | 1.3297 | 0.5113 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1011 | 129 | 0.1013 | -0.475 | 0.3178 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 1474 | 125 | 0.1243 | -0.8424 | 0.224 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 536 | 124 | 1.5286 | 2.3524 | 0.6048 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1841 | 112 | -0.541 | -1.709 | 0.1518 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 97 | 97 | -0.3224 | -1.9932 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 719 | 89 | 1.1645 | 1.2266 | 0.4382 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 183 | 82 | 1.705 | 2.6772 | 0.5854 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_high` | 1146 | 82 | -0.5993 | -1.8278 | 0.1463 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 531 | 81 | 0.0725 | 0.7958 | 0.4568 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 687 | 73 | -0.2871 | -1.4622 | 0.1781 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 53 | 53 | -0.2921 | -3.3492 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 32 | 32 | 1.2316 | 1.6911 | 0.5938 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 28 | 28 | 0.8427 | 0.9759 | 0.5714 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 124, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 726 | 462 | -0.5708 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 694 | 462 | -0.5708 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 694 | 462 | -0.5708 | `keep_collecting` |
| `latency_state` | `simulated` | 694 | 462 | -0.5708 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 726 | 462 | -0.5708 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 688 | 459 | -0.5639 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 689 | 458 | -0.567 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 686 | 452 | -0.5687 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 626 | 414 | -0.6151 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 597 | 393 | -0.6076 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 588 | 379 | -0.6208 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 513 | 347 | -0.578 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 341 | 235 | -0.6724 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 324 | 235 | -0.6724 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 324 | 235 | -0.6724 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 367 | 224 | -0.4673 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 367 | 224 | -0.4673 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 358 | 218 | -0.4414 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 253 | 151 | -0.3389 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 206 | 151 | -0.8728 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 104 | 80 | -0.2943 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 130 | 76 | -0.6794 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 89 | 64 | -0.3346 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 58 | 40 | -0.2243 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 33 | -0.96 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 74 | 31 | -0.2713 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 28 | 24 | -0.1815 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 40 | 20 | -0.7836 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 21 | 18 | -0.4643 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 24 | 16 | -0.6605 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 13 | 0.3095 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 65 | 10 | -0.6625 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 17 | 10 | -0.8307 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 10 | 8 | -0.0079 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 8 | 0.7036 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 48, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 693 | 462 | -1.1331 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 693 | 462 | -1.1331 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 591 | 389 | -1.1326 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 380 | 367 | -1.556 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 305 | 305 | -1.5494 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 89 | 62 | -1.1662 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 53 | 53 | -1.5312 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 30 | 27 | 0.7716 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 25 | 25 | 0.6939 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 28 | 23 | 0.067 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 23 | 23 | 0.067 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 22 | 20 | 2.0581 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 14 | 14 | 2.0561 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 25 | 13 | -0.8631 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 12 | -0.398 | `hold_no_edge` |
| `holding_action` | `BUY` | 13 | 11 | -0.9642 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.4824 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.9427 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -1.9216 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.4219 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 41 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 29 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 231 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 41 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 202 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 698 | 698 | -1.3555 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 455 | 455 | -0.8434 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 455 | 455 | -0.8434 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 455 | 455 | -0.8434 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 442 | 442 | -1.1627 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 319 | 319 | -1.1476 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 201 | 201 | -1.2619 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 188 | 188 | -1.7093 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 166 | 166 | -1.894 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 149 | 149 | -0.491 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 115 | 115 | -0.5312 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 105 | 105 | -1.137 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 101 | 101 | -0.5019 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 97 | 97 | -1.7329 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 68 | 68 | -1.3435 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 61 | 61 | 1.0023 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 59 | 59 | -2.6249 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 55 | 55 | -0.637 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 48 | 48 | -1.0522 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 7946 | 41 | 0.1074 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 41 | 41 | 0.1074 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 41 | 41 | 0.1074 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.7482 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 34 | 34 | -0.0098 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 33 | 33 | 0.9958 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 30 | 30 | 0.2396 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 28 | 28 | 2.6524 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 22 | 22 | 0.2209 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 13 | 13 | -0.9266 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 12 | 12 | 1.8893 | `hold_sample` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 11 | 11 | -0.8301 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 11 | 11 | -0.2864 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 11 | 11 | -0.0316 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 9 | 9 | 1.0811 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 9 | 9 | 2.9845 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 8 | 8 | -1.0275 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 7 | 7 | 0.99 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 5 | 5 | 0.7695 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 4 | 4 | 4.3515 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 550, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 17846 | 17846 | None | -0.444 | 0.2311 | `hold_sample` |
| `arm` | `AVG_DOWN` | 13668 | 13550 | None | -0.8594 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 9859 | 9859 | None | -0.3817 | 0.27 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 9918 | 9800 | None | -1.0357 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 4720 | 4310 | None | 0.864 | 0.9586 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 4720 | 4310 | None | 0.864 | 0.9586 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3750 | 3750 | None | -0.3989 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3733 | 3733 | None | -0.5193 | 0.1966 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 3391 | 3391 | None | 0.5284 | 0.9779 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2211 | 2211 | None | -0.5668 | 0.166 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1104 | 1104 | None | -0.5052 | 0.1721 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 939 | 939 | None | -0.439 | 0.1821 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 864 | 864 | None | -0.4209 | 0.0671 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 542 | 542 | None | -0.8602 | 0.107 | `hold_sample` |
| `blocker_reason` | `low_broken` | 487 | 487 | None | -0.4165 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 424 | 424 | None | 3.1575 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 366 | 366 | None | -0.4287 | 0.0847 | `hold_sample` |
| `blocker_reason` | `ok` | 301 | 301 | None | -2.6252 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 286 | 286 | None | -1.07 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.97)` | 228 | 228 | None | -0.97 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 82 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 41 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 82 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 41 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 82 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 41 | 41 | 0.1074 | 0.1432 | 0.3658 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 78 | 39 | 0.1217 | 0.1623 | 0.3846 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 58 | 29 | 0.292 | 0.3893 | 0.4138 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 52 | 26 | -0.5893 | -0.7858 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 13 | 13 | -0.9266 | -1.2354 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 26 | 13 | -0.9266 | -1.2354 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 12 | 12 | -0.2687 | -0.3583 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.2687 | -0.3583 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 6 | -0.1937 | -0.2583 | 0.5 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 5 | 5 | 0.7695 | 1.026 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 10 | 5 | 0.7695 | 1.026 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.2745 | 0.366 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 10 | 5 | 0.7695 | 1.026 | 1.0 | `hold_sample` |

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
