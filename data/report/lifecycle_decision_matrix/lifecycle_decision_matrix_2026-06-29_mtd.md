# Lifecycle Decision Matrix - 2026-06-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-29_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `252683`
- source_rows_total: `367898`
- retained_rows: `252683`
- dropped_rows_by_source: `{}`
- joined_rows: `218837`
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
- lifecycle_flow_bucket_count: `1007`
- lifecycle_flow_complete_count: `1289`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 15309 | 2052 | 0.7061 | 0.9448 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4875 | 3204 | -0.5145 | 0.9982 | `pass` | `NO_CHANGE` | False |
| `holding` | 4597 | 3204 | -0.9439 | 0.998 | `pass` | `EXIT` | False |
| `scale_in` | 207113 | 204568 | -0.4384 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 20789 | 5809 | -0.9407 | 0.9834 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 1007, 'complete_flow_count': 1289, 'incomplete_flow_count': 228000, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 160159 | 159399 | -0.7388 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 44428 | 42643 | 0.7054 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 2082 | 2082 | -1.0423 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 493 | 493 | 1.4113 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 390 | 390 | 1.6645 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 227 | 227 | 1.6843 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 186 | 186 | -0.2216 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 69 | 69 | -0.921 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 38 | 38 | -0.8637 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 31 | 31 | -1.0263 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'bucket_count': 582, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 10741 | 2043 | 0.7064 | 0.7841 | 0.4567 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 10095 | 1537 | 0.6086 | 0.3226 | 0.4385 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 1117 | 1117 | 1.5528 | 2.4841 | 0.6383 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 14374 | 1117 | 1.5528 | 2.4841 | 0.6383 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 11124 | 856 | -0.3005 | -1.2775 | 0.236 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 798 | 798 | 1.3498 | 2.174 | 0.6253 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6703 | 749 | -0.3198 | -1.3391 | 0.2203 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2890 | 721 | 1.3171 | 2.1217 | 0.6311 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 6648 | 700 | 0.0185 | -0.7552 | 0.2871 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1543 | 669 | 1.0912 | 1.6639 | 0.5785 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5774 | 624 | -0.2918 | -1.284 | 0.2308 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 3142 | 541 | 0.718 | 0.7991 | 0.488 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1370 | 485 | 0.9114 | 1.3972 | 0.5546 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 6622 | 457 | -0.3494 | -1.4213 | 0.2035 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 450 | 450 | -0.2234 | -1.9922 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2652 | 403 | 0.4392 | 0.1703 | 0.3921 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 627 | 313 | 1.3642 | 2.0464 | 0.5974 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1631 | 271 | 0.7932 | 1.2143 | 0.4908 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 233 | 233 | -0.2612 | -3.043 | 0.0 | `hold_sample` |
| `score_band` | `score_63_65` | 1067 | 233 | 0.8532 | 1.2358 | 0.4979 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 1844 | 217 | 0.0179 | -0.1364 | 0.3502 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 212 | 212 | -0.5231 | 2.0692 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 116 | 116 | 1.2408 | 1.7372 | 0.6379 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 197, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4715 | 3204 | -0.5145 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 4315 | 3204 | -0.5145 | `keep_collecting` |
| `latency_state` | `simulated` | 4315 | 3204 | -0.5145 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4698 | 3204 | -0.5145 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4266 | 3169 | -0.5009 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 4000 | 2988 | -0.5323 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3671 | 2717 | -0.5235 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3534 | 2602 | -0.5525 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2616 | 1952 | -0.5448 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2361 | 1786 | -0.6594 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2206 | 1786 | -0.6594 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2206 | 1786 | -0.6594 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2325 | 1695 | -0.4209 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2024 | 1535 | -0.6641 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1954 | 1441 | -0.394 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2074 | 1415 | -0.332 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 2074 | 1415 | -0.332 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1766 | 1364 | -0.6141 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1735 | 1181 | -0.3084 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1337 | 962 | -0.4039 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1250 | 914 | -0.5379 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 763 | 567 | -0.2644 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 829 | 487 | -0.4646 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 403 | 322 | -0.6757 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 440 | 283 | -0.1487 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 788 | 219 | -0.2695 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 315 | 216 | -0.2686 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 315 | 216 | -0.2686 | `keep_collecting` |
| `would_limit_fill` | `false` | 868 | 210 | -0.2766 | `keep_collecting` |
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
| `held_bucket` | `held_not_applicable_at_start` | 4314 | 3204 | -0.9439 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4314 | 3204 | -0.9439 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2493 | 2387 | -1.4499 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2086 | 1557 | -1.0264 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 2017 | 1473 | -0.8426 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1168 | 1168 | -1.5038 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1071 | 1071 | -1.3909 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 267 | 244 | 0.2199 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 222 | 210 | 0.6249 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 211 | 174 | -1.0639 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 216 | 156 | 0.0291 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 148 | 148 | -1.451 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 140 | 132 | 2.117 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 118 | 118 | 0.3213 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 106 | 106 | 0.7217 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 149 | 75 | -0.4321 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 69 | 69 | 2.2866 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 59 | 59 | 0.0068 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 54 | 54 | 1.9509 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 50 | 50 | -0.482 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.8122 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 283 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 73 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 204 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1110 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 283 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 544 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 529 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 4306 | 4306 | -1.3343 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3031 | 3031 | -1.0046 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2495 | 2495 | -0.9584 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2495 | 2495 | -0.9584 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2495 | 2495 | -0.9584 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1851 | 1851 | -1.1943 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1347 | 1347 | -1.2812 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1177 | 1177 | -1.5071 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1063 | 1063 | -0.5127 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 920 | 920 | -1.81 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 791 | 791 | -0.9178 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 647 | 647 | 0.6057 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 639 | 639 | -0.5092 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 552 | 552 | -0.5334 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 495 | 495 | -1.7194 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 447 | 447 | -1.1719 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 404 | 404 | -0.8684 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 399 | 399 | -1.2583 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 368 | 368 | -2.465 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 15263 | 283 | -0.1006 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 283 | 283 | -0.1006 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 283 | 283 | -0.1006 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 263 | 263 | 0.2616 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 227 | 227 | 0.0648 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 227 | 227 | 0.7438 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 153 | 153 | -1.6731 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 147 | 147 | 2.4077 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 106 | 106 | -0.9541 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 93 | 93 | -0.4084 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 93 | 93 | 0.1267 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 79 | 79 | 1.2155 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 73 | 73 | -0.287 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 63 | 63 | 0.3271 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 60 | 60 | 0.801 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 57 | 57 | 2.5345 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 54 | 54 | 1.0306 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 49 | 49 | 0.2598 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 1181, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 204519 | 204519 | None | -0.5048 | 0.2043 | `hold_sample` |
| `arm` | `AVG_DOWN` | 162468 | 161708 | None | -0.8093 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 116213 | 116213 | None | -0.5029 | 0.2046 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 114787 | 114027 | None | -0.9705 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 47681 | 47681 | None | -0.4237 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 44645 | 42860 | None | 0.6455 | 0.976 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 44645 | 42860 | None | 0.6455 | 0.976 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 38656 | 38656 | None | -0.4853 | 0.2104 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 36012 | 36012 | None | 0.5178 | 0.9813 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 26229 | 26229 | None | -0.5186 | 0.205 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 19369 | 19369 | None | -0.3336 | 0.1573 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 13008 | 13008 | None | -0.5149 | 0.1905 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10413 | 10413 | None | -0.5512 | 0.1949 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4531 | 4531 | None | -0.4567 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2892 | 2892 | None | -0.8391 | 0.0892 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `blocker_reason` | `ok` | 1838 | 1838 | None | -2.415 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1672 | 1672 | None | 3.2184 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1595 | 1595 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1526 | 1526 | None | -0.96 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 566 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 283 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 566 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 283 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 566 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 283 | 283 | -0.1006 | -0.1341 | 0.3357 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 556 | 278 | -0.0993 | -0.1324 | 0.3417 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 408 | 204 | -0.0257 | -0.0343 | 0.3677 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 376 | 188 | -0.6517 | -0.8689 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 106 | 106 | -0.9541 | -1.2721 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 212 | 106 | -0.9541 | -1.2721 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 74 | 74 | -0.2841 | -0.3788 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 148 | 74 | -0.2841 | -0.3788 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 146 | 73 | -0.2783 | -0.3711 | 0.274 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 60 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 120 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 104 | 52 | 0.274 | 0.3654 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 23 | 23 | 0.8494 | 1.1326 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 46 | 23 | 0.8494 | 1.1326 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 46 | 23 | 0.8494 | 1.1326 | 1.0 | `hold_sample` |

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
