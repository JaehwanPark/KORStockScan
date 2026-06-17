# Lifecycle Decision Matrix - 2026-06-17

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-17_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `65555`
- source_rows_total: `83648`
- retained_rows: `65555`
- dropped_rows_by_source: `{}`
- joined_rows: `59551`
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
- lifecycle_flow_bucket_count: `315`
- lifecycle_flow_complete_count: `310`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0051`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4087 | 468 | 1.0202 | 0.9911 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 820 | 512 | -0.3814 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 763 | 512 | -0.8181 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 58309 | 57224 | -0.4535 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1576 | 835 | -0.858 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 315, 'complete_flow_count': 310, 'incomplete_flow_count': 60162, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 47132 | 46861 | -0.7057 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 10818 | 10004 | 0.738 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 290 | 290 | -1.0071 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 102 | 102 | 1.8848 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 87 | 87 | 1.7773 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 62 | 62 | 2.4752 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 20 | 20 | 0.3233 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 14 | 14 | -0.9707 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 10 | 10 | -2.198 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 9 | 9 | -0.8795 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 8 | 8 | -1.2809 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 8 | 8 | -0.87 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 8 | 8 | -0.8975 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -1.2062 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.436 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 6 | 6 | -0.5897 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 6 | 6 | -1.3538 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 6 | 6 | -0.3088 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 5 | 5 | -2.5938 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 5 | 5 | -0.5168 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 312, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3121 | 464 | 1.0296 | 1.1546 | 0.4957 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 3281 | 395 | 0.7555 | 0.5638 | 0.4709 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 255 | 255 | 1.9611 | 2.9422 | 0.6902 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 3874 | 255 | 1.9611 | 2.9422 | 0.6902 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 3419 | 191 | -0.0477 | -1.1098 | 0.2513 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 2111 | 130 | 0.2247 | -0.5076 | 0.3077 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 2292 | 129 | -0.0523 | -1.0232 | 0.248 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2014 | 129 | -0.0523 | -1.0232 | 0.248 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 352 | 122 | 1.7043 | 2.542 | 0.6639 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 122 | 122 | 1.7043 | 2.542 | 0.6639 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 313 | 116 | 1.1745 | 2.0206 | 0.6724 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 355 | 114 | 1.4222 | 2.0846 | 0.6228 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 105 | 105 | 0.0133 | -1.9424 | 0.0 | `hold_no_edge` |
| `score_band` | `score_60_62` | 1673 | 71 | 0.0352 | -1.5062 | 0.1831 | `hold_no_edge` |
| `score_band` | `score_66_69` | 148 | 62 | 1.4136 | 1.9337 | 0.5484 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 60 | 60 | 1.5735 | 2.1006 | 0.6166 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 54 | 54 | -0.2594 | 2.3265 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 50 | 50 | 1.9886 | 2.9546 | 0.86 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 251 | 48 | 0.5089 | -1.2414 | 0.2292 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 316 | 45 | 0.9235 | 0.9506 | 0.4667 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 44 | 44 | -0.3123 | -2.9766 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 476 | 43 | 0.7742 | 0.4902 | 0.4186 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 40 | 40 | 1.4633 | 1.9246 | 0.675 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 577 | 37 | -0.1363 | -0.866 | 0.2973 | `hold_no_edge` |
| `score_band` | `score_lt60` | 621 | 23 | -0.0685 | -0.723 | 0.3044 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 496 | 22 | -0.1451 | -1.4014 | 0.1818 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 415 | 22 | -0.0626 | -1.4936 | 0.1364 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 98, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 803 | 512 | -0.3814 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 712 | 512 | -0.3814 | `keep_collecting` |
| `latency_state` | `simulated` | 712 | 512 | -0.3814 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 801 | 512 | -0.3814 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 709 | 509 | -0.3712 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 646 | 464 | -0.3946 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 601 | 425 | -0.3965 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 578 | 406 | -0.395 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 511 | 368 | -0.2897 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 451 | 325 | -0.2803 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 406 | 287 | -0.3919 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 418 | 279 | -0.1706 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 418 | 279 | -0.1706 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 330 | 233 | -0.6338 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 294 | 233 | -0.6338 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 294 | 233 | -0.6338 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 350 | 229 | -0.1307 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 236 | 173 | -0.3965 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 193 | 137 | -0.6594 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 165 | 126 | -0.7096 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 134 | 103 | -0.2777 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 111 | 87 | -0.3078 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 57 | -0.5425 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 174 | 48 | -0.2541 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 66 | 48 | -0.2541 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 174 | 48 | -0.2541 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 66 | 48 | -0.2541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 42 | 42 | -0.1886 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 42 | 32 | -0.4812 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 48 | 30 | -0.2255 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 23 | 23 | -0.0931 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 712 | 512 | -0.8181 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 712 | 512 | -0.8181 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 402 | 384 | -1.2932 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 486 | 348 | -0.8132 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 265 | 265 | -1.2569 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 210 | 151 | -0.839 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 108 | 108 | -1.3827 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 39 | 38 | 0.3806 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 33 | 33 | 0.6675 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 28 | 28 | 0.3693 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 23 | 23 | 1.9699 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 20 | 20 | 0.6544 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 38 | 19 | -0.36 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 28 | 15 | 0.1817 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 15 | 15 | 2.0791 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 16 | 13 | -0.706 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 13 | 13 | -0.3954 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 12 | 12 | 0.6865 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.2873 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 10 | 10 | 0.4123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | 0.2675 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 7 | 7 | 0.0838 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 7 | 7 | 1.4059 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 6 | 6 | -0.2833 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 4.2814 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 51 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 46 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 200 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 51 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 138 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 59 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 57, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 629 | 629 | -1.2295 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 435 | 435 | -0.8679 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 349 | 349 | -0.9277 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 349 | 349 | -0.9277 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 349 | 349 | -0.9277 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 266 | 266 | -1.1352 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 217 | 217 | -1.1251 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 156 | 156 | -1.3652 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 141 | 141 | -0.366 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 138 | 138 | -0.8185 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 118 | 118 | -1.7762 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 95 | 95 | -1.04 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 90 | 90 | -0.4932 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 89 | 89 | 0.877 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 71 | 71 | -0.553 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 63 | 63 | -0.8498 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 59 | 59 | -1.5561 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 55 | 55 | -2.4515 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 792 | 51 | -0.2976 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 51 | 51 | -0.2976 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 51 | 51 | -0.2976 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 47 | 47 | -1.0663 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 40 | 40 | 0.497 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 34 | 34 | 0.7181 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 24 | 24 | 2.2121 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 19 | 19 | -0.27 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 19 | 19 | 0.3465 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 18 | 18 | 0.2153 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 18 | 18 | -0.7883 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 16 | 16 | -1.5404 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 14 | 14 | 0.0963 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 13 | 13 | 0.2498 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 12 | 12 | 2.7288 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 12 | 12 | 0.4295 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 8 | 8 | 0.7941 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 8 | 8 | 0.9518 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 8 | 8 | 1.2953 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -0.3639 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 5 | 5 | 0.974 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 300, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 57202 | 57202 | None | -0.5112 | 0.1717 | `hold_sample` |
| `arm` | `AVG_DOWN` | 47465 | 47194 | None | -0.7649 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 38594 | 38594 | None | -0.5022 | 0.177 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 32725 | 32454 | None | -0.9165 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 14740 | 14740 | None | -0.431 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 10844 | 10030 | None | 0.686 | 0.9812 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 10844 | 10030 | None | 0.686 | 0.9812 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 8895 | 8895 | None | -0.5196 | 0.1654 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 7855 | 7855 | None | -0.3562 | 0.1212 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 7808 | 7808 | None | 0.4845 | 0.9868 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 4231 | 4231 | None | -0.5583 | 0.138 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2782 | 2782 | None | -0.4909 | 0.1787 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2700 | 2700 | None | -0.5601 | 0.1629 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1077 | 1077 | None | -0.4803 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 764 | 764 | None | 3.1594 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 484 | 484 | None | -0.376 | 0.3657 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 427 | 427 | None | -0.92 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 422 | 422 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 420 | 420 | None | -0.93 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 408 | 408 | None | -0.75 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 27, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 102 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 51 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 102 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 51 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 102 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 102 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 51 | 51 | -0.2976 | -0.3969 | 0.2549 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 92 | 46 | -0.2838 | -0.3785 | 0.2826 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 76 | 38 | -0.5088 | -0.6784 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 19 | 19 | -0.27 | -0.36 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 38 | 19 | -0.27 | -0.36 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 18 | 18 | -0.7883 | -1.0511 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 36 | 18 | -0.7883 | -1.0511 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 13 | 13 | 0.2498 | 0.3331 | 0.9231 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 26 | 13 | 0.2498 | 0.3331 | 0.9231 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 24 | 12 | 0.2719 | 0.3625 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 5 | -0.4245 | -0.566 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 2 | 1 | 0.8925 | 1.19 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 1 | 0.8925 | 1.19 | 1.0 | `hold_sample` |

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
