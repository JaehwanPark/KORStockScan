# Lifecycle Decision Matrix - 2026-06-30

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-30_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `258514`
- source_rows_total: `385904`
- retained_rows: `258514`
- dropped_rows_by_source: `{}`
- joined_rows: `222070`
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
- lifecycle_flow_bucket_count: `1046`
- lifecycle_flow_complete_count: `1299`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0055`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 15564 | 2084 | 0.7109 | 0.9365 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 5021 | 3240 | -0.5173 | 0.997 | `pass` | `NO_CHANGE` | False |
| `holding` | 4687 | 3240 | -0.9443 | 0.998 | `pass` | `EXIT` | False |
| `scale_in` | 210199 | 207625 | -0.4428 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 23043 | 5881 | -0.941 | 0.9742 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 1046, 'complete_flow_count': 1299, 'incomplete_flow_count': 233468, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 162591 | 161809 | -0.7436 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 45032 | 43240 | 0.7039 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 2123 | 2123 | -1.0418 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 503 | 503 | 1.4036 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 396 | 396 | 1.6432 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 235 | 235 | 1.7222 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 191 | 191 | -0.2202 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 70 | 70 | -0.9186 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 40 | 40 | -0.8535 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 33 | 33 | -1.0314 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 24 | 24 | -1.9926 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 18 | 18 | -0.9387 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 17 | 17 | -0.5952 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 16 | 16 | -0.8968 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 16 | 16 | -1.3182 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 15 | 15 | -0.8072 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 14 | 14 | -0.2743 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 600, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 10858 | 2075 | 0.7112 | 0.8001 | 0.4598 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 10191 | 1563 | 0.6085 | 0.3438 | 0.4427 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 1160 | 1141 | 1.5501 | 2.4828 | 0.6389 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 14621 | 1141 | 1.5501 | 2.4828 | 0.6389 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 11255 | 863 | -0.3015 | -1.2685 | 0.2387 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 822 | 822 | 1.352 | 2.1813 | 0.6265 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6810 | 757 | -0.3185 | -1.3247 | 0.2246 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2976 | 745 | 1.3206 | 2.1314 | 0.6322 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 6738 | 709 | 0.0251 | -0.7257 | 0.292 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1577 | 687 | 1.0686 | 1.6347 | 0.5793 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5810 | 627 | -0.2942 | -1.2747 | 0.2328 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 3207 | 549 | 0.7309 | 0.828 | 0.4918 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1466 | 496 | 0.9145 | 1.3985 | 0.5544 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 6706 | 463 | -0.3476 | -1.4076 | 0.2073 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 453 | 453 | -0.2176 | -2.0033 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2681 | 407 | 0.4422 | 0.1616 | 0.3931 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 651 | 319 | 1.3434 | 2.0402 | 0.6019 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1682 | 275 | 0.8423 | 1.2693 | 0.4909 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 1094 | 242 | 0.9072 | 1.3311 | 0.5083 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 233 | 233 | -0.2612 | -3.043 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1924 | 232 | 0.0472 | -0.0186 | 0.3707 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 217 | 217 | -0.5276 | 2.0731 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 118 | 118 | 1.2851 | 1.8007 | 0.6441 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 203, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4805 | 3240 | -0.5173 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 4401 | 3240 | -0.5173 | `keep_collecting` |
| `latency_state` | `simulated` | 4401 | 3240 | -0.5173 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4788 | 3240 | -0.5173 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4352 | 3205 | -0.5039 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 4022 | 2996 | -0.5376 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3672 | 2717 | -0.5235 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3574 | 2618 | -0.5578 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2631 | 1958 | -0.5513 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2380 | 1793 | -0.6661 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2225 | 1793 | -0.6661 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2225 | 1793 | -0.6661 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2401 | 1727 | -0.4268 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2046 | 1543 | -0.6737 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2141 | 1444 | -0.333 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 2141 | 1444 | -0.333 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1954 | 1441 | -0.394 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1776 | 1368 | -0.6153 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1738 | 1182 | -0.3111 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1423 | 998 | -0.4171 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1305 | 915 | -0.538 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 809 | 587 | -0.2637 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 971 | 522 | -0.4798 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 403 | 322 | -0.6757 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 440 | 283 | -0.1487 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 855 | 247 | -0.2695 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 379 | 244 | -0.2687 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 379 | 244 | -0.2687 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 950 | 218 | -0.2934 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 53, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 4400 | 3240 | -0.9443 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4400 | 3240 | -0.9443 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2512 | 2405 | -1.4552 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2088 | 1558 | -1.0248 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 2101 | 1508 | -0.8473 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1168 | 1168 | -1.5038 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1089 | 1089 | -1.4037 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 277 | 253 | 0.2031 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 225 | 213 | 0.6491 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 211 | 174 | -1.0639 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 216 | 156 | 0.0291 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 148 | 148 | -1.451 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 144 | 136 | 2.0515 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 126 | 126 | 0.2722 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 123 | 123 | 0.1157 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 109 | 109 | 0.7662 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 153 | 77 | -0.4282 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 73 | 73 | 2.1553 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 59 | 59 | 0.0068 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 54 | 54 | 1.9509 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 52 | 52 | -0.4742 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.8122 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 287 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 74 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 207 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1160 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 287 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 593 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 530 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 86, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 4344 | 4344 | -1.3372 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3048 | 3048 | -1.0061 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2546 | 2546 | -0.9576 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2546 | 2546 | -0.9576 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2546 | 2546 | -0.9576 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1879 | 1879 | -1.1979 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1353 | 1353 | -1.284 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1183 | 1183 | -1.5085 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1069 | 1069 | -0.5156 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 923 | 923 | -1.8154 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 796 | 796 | -0.9181 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 661 | 661 | -0.5081 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 655 | 655 | 0.5987 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 572 | 572 | -0.5323 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 496 | 496 | -1.7208 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 450 | 450 | -1.1743 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 406 | 406 | -0.8751 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 401 | 401 | -1.2657 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 369 | 369 | -2.4719 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 17449 | 287 | -0.1022 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 287 | 287 | -0.1022 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 287 | 287 | -0.1022 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 268 | 268 | 0.2558 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 229 | 229 | 0.0647 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 228 | 228 | 0.7508 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 153 | 153 | -1.6731 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 151 | 151 | 2.3595 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 107 | 107 | -0.9569 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 95 | 95 | -0.4163 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 93 | 93 | 0.1267 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 80 | 80 | 1.2296 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 75 | 75 | -0.2849 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 64 | 64 | 0.3087 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 61 | 61 | 0.8097 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 57 | 57 | 2.5345 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 56 | 56 | 0.965 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 51 | 51 | 0.252 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 1222, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 207576 | 207576 | None | -0.5095 | 0.2041 | `hold_sample` |
| `arm` | `AVG_DOWN` | 164945 | 164163 | None | -0.8145 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 118538 | 118538 | None | -0.5086 | 0.2045 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 117195 | 116413 | None | -0.973 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 47750 | 47750 | None | -0.428 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 45254 | 43462 | None | 0.6439 | 0.9758 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 45254 | 43462 | None | 0.6439 | 0.9758 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 39069 | 39069 | None | -0.4894 | 0.21 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 36579 | 36579 | None | 0.5166 | 0.9809 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 26409 | 26409 | None | -0.522 | 0.2043 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 19396 | 19396 | None | -0.3371 | 0.1571 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 13107 | 13107 | None | -0.5159 | 0.1905 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10453 | 10453 | None | -0.5551 | 0.1945 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4535 | 4535 | None | -0.4591 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2944 | 2944 | None | -0.8364 | 0.0893 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `blocker_reason` | `ok` | 1847 | 1847 | None | -2.4246 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1678 | 1678 | None | 3.2194 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1611 | 1611 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1561 | 1561 | None | -0.96 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 574 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 287 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 574 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 287 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 574 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 287 | 287 | -0.1022 | -0.1362 | 0.3345 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 564 | 282 | -0.1009 | -0.1345 | 0.3404 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 414 | 207 | -0.0234 | -0.0312 | 0.3672 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 382 | 191 | -0.6502 | -0.867 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 107 | 107 | -0.9569 | -1.2759 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 214 | 107 | -0.9569 | -1.2759 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 76 | 76 | -0.2822 | -0.3762 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 152 | 76 | -0.2822 | -0.3762 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 148 | 74 | -0.2916 | -0.3888 | 0.2703 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 60 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 120 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 104 | 52 | 0.274 | 0.3654 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 24 | 24 | 0.8484 | 1.1313 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 48 | 24 | 0.8484 | 1.1313 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 48 | 24 | 0.8484 | 1.1313 | 1.0 | `hold_sample` |

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
