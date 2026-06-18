# Lifecycle Decision Matrix - 2026-06-18

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-18_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `86842`
- source_rows_total: `121038`
- retained_rows: `86842`
- dropped_rows_by_source: `{}`
- joined_rows: `79134`
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
- lifecycle_flow_bucket_count: `412`
- lifecycle_flow_complete_count: `412`
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
| `entry` | 5288 | 596 | 1.1709 | 0.993 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1184 | 713 | -0.4065 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1092 | 713 | -0.8224 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 76917 | 75811 | -0.4536 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2361 | 1301 | -0.8572 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 412, 'complete_flow_count': 412, 'incomplete_flow_count': 79627, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 62101 | 61810 | -0.697 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 14191 | 13376 | 0.6847 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 516 | 516 | -0.9697 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 143 | 143 | 2.1366 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 130 | 130 | 1.8894 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 76 | 76 | 2.1721 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 36 | 36 | -0.0704 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 21 | 21 | -0.8952 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 19 | 19 | -0.7452 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 12 | 12 | -2.2561 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 10 | 10 | -0.9068 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.209 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 10 | 10 | -0.911 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 9 | 9 | -1.3358 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 8 | 8 | -1.2062 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 7 | 7 | -2.5363 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.436 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 7 | 7 | -0.5599 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 6 | 6 | -0.3088 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 5 | 5 | -0.5168 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 339, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3865 | 591 | 1.1644 | 1.3831 | 0.5228 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 4087 | 498 | 0.8334 | 0.725 | 0.496 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 354 | 354 | 2.0506 | 3.0834 | 0.709 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 5046 | 354 | 2.0506 | 3.0834 | 0.709 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 727 | 221 | 1.9628 | 2.9475 | 0.7059 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 221 | 221 | 1.9628 | 2.9475 | 0.7059 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 4194 | 210 | -0.0621 | -1.1062 | 0.2524 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 501 | 202 | 1.7713 | 2.6003 | 0.6683 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 559 | 173 | 1.3607 | 2.1257 | 0.6532 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 2820 | 168 | 0.303 | -0.3322 | 0.3274 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 2942 | 158 | -0.0773 | -1.1037 | 0.2342 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2638 | 158 | -0.0773 | -1.1037 | 0.2342 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 890 | 124 | 1.5793 | 2.1792 | 0.621 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 121 | 121 | -0.0006 | -1.9344 | 0.0 | `hold_no_edge` |
| `score_band` | `score_66_69` | 233 | 104 | 1.9251 | 2.8138 | 0.6538 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 85 | 85 | 1.6018 | 2.1653 | 0.6588 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 2326 | 83 | -0.0019 | -1.49 | 0.1807 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 77 | 77 | 1.8461 | 2.8199 | 0.8312 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 59 | 59 | -0.2557 | 2.2866 | 1.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 52 | 52 | -0.3205 | -2.9333 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 50 | 50 | 1.3352 | 1.6854 | 0.64 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 251 | 48 | 0.5089 | -1.2414 | 0.2292 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 316 | 45 | 0.9235 | 0.9506 | 0.4667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 692 | 40 | -0.1473 | -0.7488 | 0.325 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 669 | 29 | -0.159 | -1.5628 | 0.1379 | `hold_no_edge` |
| `score_band` | `score_lt60` | 758 | 24 | -0.0132 | -0.5933 | 0.3333 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 415 | 22 | -0.0626 | -1.4936 | 0.1364 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 142, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1147 | 713 | -0.4065 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1015 | 713 | -0.4065 | `keep_collecting` |
| `latency_state` | `simulated` | 1015 | 713 | -0.4065 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1141 | 713 | -0.4065 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1010 | 709 | -0.3962 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 923 | 653 | -0.4194 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 865 | 599 | -0.3999 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 825 | 571 | -0.4216 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 712 | 500 | -0.3143 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 634 | 448 | -0.3064 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 611 | 424 | -0.3972 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 484 | 382 | -0.4073 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 563 | 366 | -0.1667 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 563 | 366 | -0.1667 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 509 | 347 | -0.6594 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 452 | 347 | -0.6594 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 452 | 347 | -0.6594 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 469 | 304 | -0.1303 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 357 | 223 | -0.4574 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 284 | 202 | -0.6684 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 256 | 190 | -0.6986 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 163 | 140 | -0.5989 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 190 | 138 | -0.291 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 243 | 114 | -0.4414 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 179 | 104 | 0.0432 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 133 | 95 | -0.088 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 116 | 75 | -0.9424 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 261 | 60 | -0.2655 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 92 | 60 | -0.2655 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 199 | 60 | -0.2655 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 92 | 60 | -0.2655 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 100 | 58 | -0.3232 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 35 | -0.2227 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 37 | 32 | -0.4526 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 42 | 32 | -0.4812 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 43, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1015 | 713 | -0.8224 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1015 | 713 | -0.8224 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 553 | 527 | -1.3306 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 659 | 459 | -0.81 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 346 | 346 | -1.2998 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 320 | 225 | -0.8436 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 158 | 158 | -1.3937 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 59 | 55 | 0.2937 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 49 | 49 | 0.763 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 37 | 37 | 0.2995 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 31 | 31 | 2.0476 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 36 | 29 | -0.8546 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 54 | 29 | 0.1904 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 29 | 29 | 0.7815 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 23 | 23 | -1.3618 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 44 | 22 | -0.3495 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 20 | 20 | 2.3677 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 19 | 19 | 0.7379 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 16 | 16 | 0.242 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 15 | 15 | 0.166 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 14 | 14 | -0.4021 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 13 | 13 | 0.1891 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.3395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.2575 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 2.033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 77 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 64 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 302 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 77 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 200 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 95 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 20 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 23 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 59, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 945 | 945 | -1.2446 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 614 | 614 | -0.9083 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 614 | 614 | -0.9083 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 614 | 614 | -0.9083 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 610 | 610 | -0.884 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 440 | 440 | -1.1441 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 299 | 299 | -1.1587 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 222 | 222 | -1.3899 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 200 | 200 | -0.3653 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 188 | 188 | -0.8384 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 178 | 178 | -0.5031 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 170 | 170 | -1.7749 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 156 | 156 | -0.5371 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 133 | 133 | -1.0789 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 130 | 130 | 0.852 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 84 | 84 | -0.8596 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 82 | 82 | -1.5945 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1137 | 77 | -0.2372 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 77 | 77 | -0.2372 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 77 | 77 | -0.2372 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 77 | 77 | -2.5132 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 69 | 69 | -1.0442 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 58 | 58 | 0.3722 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 52 | 52 | 0.8403 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 35 | 35 | 0.212 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 33 | 33 | 2.357 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 26 | 26 | -0.8126 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 26 | 26 | 0.375 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 25 | 25 | 0.2019 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 24 | 24 | -1.5069 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 23 | 23 | -0.0973 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 22 | 22 | -0.2622 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 17 | 17 | 1.3267 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 13 | 13 | 2.8862 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 13 | 13 | 0.4443 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 12 | 12 | 0.7352 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 12 | 12 | 0.7229 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.3467 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 7 | 7 | -0.3639 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 6 | 6 | 0.3483 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 351, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 75789 | 75789 | None | -0.5102 | 0.172 | `hold_sample` |
| `arm` | `AVG_DOWN` | 62684 | 62393 | None | -0.7548 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 50442 | 50442 | None | -0.506 | 0.1741 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 42966 | 42675 | None | -0.9062 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 19718 | 19718 | None | -0.427 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 14233 | 13418 | None | 0.6297 | 0.9729 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 14233 | 13418 | None | 0.6297 | 0.9729 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 12490 | 12490 | None | -0.5206 | 0.1612 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 10662 | 10662 | None | -0.3448 | 0.1329 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 10536 | 10536 | None | 0.476 | 0.98 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 5915 | 5915 | None | -0.5278 | 0.163 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3652 | 3652 | None | -0.4898 | 0.1818 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3290 | 3290 | None | -0.526 | 0.1863 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1580 | 1580 | None | -0.4722 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 764 | 764 | None | 3.1594 | 1.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 679 | 679 | None | -0.737 | 0.0678 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 566 | 566 | None | -0.2787 | 0.1361 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 544 | 544 | None | -0.92 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 529 | 529 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 515 | 515 | None | -1.09 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 154 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 77 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 154 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 77 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 154 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 154 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 77 | 77 | -0.2372 | -0.3162 | 0.3247 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 128 | 64 | -0.182 | -0.2427 | 0.375 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 104 | 52 | -0.5204 | -0.6938 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 26 | 26 | -0.8126 | -1.0835 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 52 | 26 | -0.8126 | -1.0835 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 25 | 25 | 0.2019 | 0.2692 | 0.84 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 50 | 25 | 0.2019 | 0.2692 | 0.84 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 22 | 22 | -0.2622 | -0.3495 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 44 | 22 | -0.2622 | -0.3495 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 42 | 21 | 0.2482 | 0.331 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 26 | 13 | -0.5089 | -0.6785 | 0.0769 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.8962 | 1.195 | 1.0 | `hold_sample` |

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
