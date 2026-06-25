# Lifecycle Decision Matrix - 2026-06-25

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-25_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `25223`
- source_rows_total: `31265`
- retained_rows: `25223`
- dropped_rows_by_source: `{}`
- joined_rows: `16071`
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
- lifecycle_flow_bucket_count: `251`
- lifecycle_flow_complete_count: `183`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0085`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2682 | 344 | 0.8375 | 0.9005 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 658 | 392 | -0.5828 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 648 | 392 | -1.1635 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 14502 | 14137 | -0.4659 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6733 | 806 | -0.951 | 0.9667 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 251, 'complete_flow_count': 183, 'incomplete_flow_count': 21454, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 10956 | 10851 | -0.8057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 3154 | 2894 | 0.8493 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 318 | 318 | -0.967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 103 | 103 | 1.3944 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 70 | 70 | 1.9014 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 36 | 36 | 0.1517 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 23 | 23 | 3.3492 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 13 | 13 | -0.8158 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.6133 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 6 | 6 | -0.7393 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 5 | 5 | -1.4981 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 5 | 5 | -1.31 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 4 | 4 | -1.8461 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -1.0246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 4 | 4 | -1.8443 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 3 | 3 | 2.7581 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2a4bfd22da` | 3 | 3 | -1.3519 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5a2fc3c833` | 3 | 3 | -2.8731 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 321, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1975 | 342 | 0.8496 | 1.009 | 0.4152 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1756 | 255 | 0.6957 | 0.4569 | 0.3922 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 198 | 198 | 1.7742 | 2.8744 | 0.5959 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2536 | 198 | 1.7742 | 2.8744 | 0.5959 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 198 | 198 | 1.7742 | 2.8744 | 0.5959 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1552 | 146 | -0.433 | -1.5603 | 0.1712 | `hold_no_edge` |
| `score_band` | `score_70p` | 375 | 134 | 0.9857 | 1.3989 | 0.5 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1956 | 128 | -0.4784 | -1.5785 | 0.1797 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 348 | 122 | 1.2861 | 1.9143 | 0.5328 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 466 | 121 | 1.8496 | 3.0085 | 0.6116 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 813 | 118 | 0.23 | -0.2293 | 0.3475 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 1142 | 98 | 0.2802 | -0.6108 | 0.2245 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1494 | 84 | -0.5011 | -1.9016 | 0.119 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 431 | 77 | 0.9554 | 2.1274 | 0.4935 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 77 | 77 | -0.3357 | -2.01 | 0.0 | `hold_no_edge` |
| `score_band` | `score_66_69` | 152 | 74 | 1.7883 | 2.9444 | 0.554 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 569 | 67 | 1.0324 | 1.1514 | 0.4329 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_high` | 830 | 59 | -0.5899 | -2.0171 | 0.1356 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 552 | 57 | -0.3175 | -1.4 | 0.1754 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 41 | 41 | -0.3462 | -3.3317 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 30 | 30 | 0.922 | 1.0385 | 0.6333 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 30 | 30 | 1.5283 | 2.3629 | 0.6333 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 16 | 16 | 1.7477 | 2.88 | 0.6875 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 118, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 642 | 392 | -0.5828 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 612 | 392 | -0.5828 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 612 | 392 | -0.5828 | `keep_collecting` |
| `latency_state` | `simulated` | 612 | 392 | -0.5828 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 642 | 392 | -0.5828 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 608 | 389 | -0.5779 | `source_quality_workorder` |
| `overbought_guard_action` | `would_pass` | 606 | 389 | -0.5747 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 604 | 383 | -0.5801 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 546 | 346 | -0.6325 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 518 | 326 | -0.6238 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 511 | 312 | -0.6405 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 453 | 298 | -0.5896 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 309 | 210 | -0.669 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 293 | 210 | -0.669 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 293 | 210 | -0.669 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 316 | 179 | -0.4856 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 316 | 179 | -0.4856 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 308 | 174 | -0.4531 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 186 | 135 | -0.8837 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 215 | 118 | -0.3288 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 99 | 77 | -0.3081 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 87 | 62 | -0.3543 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 111 | 58 | -0.7173 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 57 | 39 | -0.2352 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 63 | 29 | -0.2907 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 38 | 24 | -1.1107 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 27 | 24 | -0.1815 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 18 | -0.4643 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 22 | 14 | -0.7562 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 33 | 13 | -0.7778 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 13 | 0.3095 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 54 | 9 | -0.6944 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 15 | 8 | -1.1074 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 12 | 8 | 0.7036 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 9 | 7 | -0.0597 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 611 | 392 | -1.1635 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 611 | 392 | -1.1635 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 515 | 325 | -1.1419 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 321 | 310 | -1.5722 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 252 | 252 | -1.5616 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 86 | 59 | -1.1639 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 50 | 50 | -1.5504 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 28 | 25 | 0.7423 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 23 | 23 | 0.6553 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 21 | 17 | 0.0334 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.0334 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 16 | 15 | 1.8776 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 25 | 13 | -0.8631 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 18 | 12 | -0.398 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 11 | 11 | -0.4824 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.9427 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 11 | 11 | 2.0433 | `hold_sample` |
| `holding_action` | `BUY` | 10 | 8 | -2.0407 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 8 | 8 | -2.0407 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 1.4219 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 2 | 2 | 1.7422 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 37 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 219 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 190 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 27 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_020_180s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 64, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 595 | 595 | -1.3666 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 392 | 392 | -0.8272 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 392 | 392 | -0.8272 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 392 | 392 | -0.8272 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 377 | 377 | -1.1739 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 272 | 272 | -1.1588 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 169 | 169 | -1.2748 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 156 | 156 | -1.7504 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 144 | 144 | -1.8886 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 133 | 133 | -0.4738 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 99 | 99 | -0.5301 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 88 | 88 | -1.21 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 85 | 85 | -0.4951 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 81 | 81 | -1.7409 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 62 | 62 | -1.3313 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 53 | 53 | 1.0368 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 48 | 48 | -2.6699 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 48 | 48 | -0.6494 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.1093 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 5964 | 37 | 0.0091 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 37 | 37 | 0.0091 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 37 | 37 | 0.0091 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 34 | 34 | -0.0098 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 34 | 34 | -1.802 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 31 | 31 | 0.9867 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 24 | 24 | 0.2695 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 23 | 23 | 2.7116 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 22 | 22 | 0.2209 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 11 | 11 | -0.9552 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 11 | 11 | -0.2864 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 11 | 11 | 1.9429 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 10 | 10 | -0.1323 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 9 | 9 | -1.254 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 9 | 9 | 2.9845 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 7 | 7 | 0.99 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 7 | 7 | -0.7939 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 7 | 7 | 0.6898 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 4 | 4 | 4.3515 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 470, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 14127 | 14127 | None | -0.5125 | 0.2001 | `hold_sample` |
| `arm` | `AVG_DOWN` | 11305 | 11200 | None | -0.8616 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8018 | 7913 | None | -1.0542 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 7650 | 7650 | None | -0.4761 | 0.2285 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3287 | 3287 | None | -0.3979 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 3009 | 3009 | None | -0.5448 | 0.1815 | `hold_sample` |
| `arm` | `PYRAMID` | 3197 | 2937 | None | 0.8207 | 0.9642 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 3197 | 2937 | None | 0.8207 | 0.9642 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 2367 | 2367 | None | 0.4862 | 0.9717 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1834 | 1834 | None | -0.6081 | 0.1538 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 858 | 858 | None | -0.5529 | 0.1492 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 776 | 776 | None | -0.4771 | 0.1585 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 714 | 714 | None | -0.4075 | 0.0728 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 474 | 474 | None | -0.8655 | 0.1118 | `hold_sample` |
| `blocker_reason` | `low_broken` | 380 | 380 | None | -0.419 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 286 | 286 | None | -1.07 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 257 | 257 | None | -2.6358 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 253 | 253 | None | 3.5805 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 223 | 223 | None | -0.5762 | 0.1121 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 187 | 187 | None | -0.307 | 0.3262 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 74 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 37 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 74 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 37 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 74 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 37 | 37 | 0.0091 | 0.0122 | 0.3513 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 70 | 35 | 0.0195 | 0.026 | 0.3714 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 52 | 26 | 0.1477 | 0.1969 | 0.3846 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 48 | 24 | -0.5744 | -0.7658 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 12 | 12 | -0.2687 | -0.3583 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 24 | 12 | -0.2687 | -0.3583 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 11 | 11 | -0.9552 | -1.2736 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 22 | 11 | -0.9552 | -1.2736 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.12 | -0.16 | 0.6 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.2745 | 0.366 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 8 | 4 | -0.4594 | -0.6125 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.7725 | 1.03 | 1.0 | `hold_sample` |

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
