# Lifecycle Decision Matrix - 2026-06-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-01_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `70684`
- source_rows_total: `89479`
- retained_rows: `70684`
- dropped_rows_by_source: `{}`
- joined_rows: `68089`
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
- lifecycle_flow_bucket_count: `243`
- lifecycle_flow_complete_count: `273`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0059`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2116 | 432 | 0.9134 | 1.0 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 816 | 740 | -0.6243 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 786 | 740 | -0.7359 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 64157 | 64108 | -0.243 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2809 | 2069 | -0.6378 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 243, 'complete_flow_count': 273, 'incomplete_flow_count': 45617, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 31712 | 31684 | -0.6745 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 11356 | 11343 | 0.6721 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 529 | 529 | -0.8355 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 199 | 199 | 1.1369 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 118 | 118 | 1.5523 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 57 | 57 | -0.1179 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 26 | 26 | 0.6525 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:88611b572d` | 9 | 9 | -2.5761 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 9 | 9 | -0.6156 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:42075e2cfd` | 7 | 7 | -1.169 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fd9360c39d` | 7 | 7 | 0.1575 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:87c84ee9f7` | 7 | 7 | -0.5029 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7c897ec6ef` | 6 | 6 | -2.3006 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:93f13405b3` | 6 | 6 | -0.8792 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:4ce5e1021f` | 6 | 6 | -1.3512 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 6 | 6 | -0.6117 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:07dd4b972c` | 5 | 5 | -0.7142 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:438a0575a6` | 5 | 5 | -0.3313 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b85b2fccd5` | 5 | 5 | 2.3307 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 5 | 5 | -0.728 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 247, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 343 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_unknown` | 2027 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 1039 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 343 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 343 | 343 | 1.243 | 2.1276 | 0.5364 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 379 | 292 | 1.3376 | 2.3085 | 0.5377 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 567 | 224 | 0.9413 | 1.7654 | 0.5357 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 175 | 175 | 1.2604 | 2.0603 | 0.5486 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 172 | 123 | 1.5219 | 2.4283 | 0.5285 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 437 | 92 | 0.2278 | 0.4198 | 0.4782 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1077 | 89 | -0.3569 | -0.8273 | 0.3371 | `hold_no_edge` |
| `strength_bucket` | `risk_unknown` | 738 | 89 | -0.3569 | -0.8273 | 0.3371 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 738 | 89 | -0.3569 | -0.8273 | 0.3371 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_watch` | 88 | 88 | 1.4491 | 2.4486 | 0.5341 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 814 | 85 | -0.3444 | -0.7512 | 0.3529 | `hold_no_edge` |
| `overbought_bucket` | `overbought_unknown` | 655 | 74 | -0.2486 | -0.7309 | 0.3513 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 412 | 71 | -0.4367 | -0.4245 | 0.4225 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 1042 | 66 | -0.2928 | -1.0708 | 0.2727 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 56 | 56 | 1.0461 | 2.0498 | 0.5357 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 1025 | 44 | -0.3491 | -1.1855 | 0.2727 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 284 | 39 | 0.0658 | 0.2921 | 0.4616 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 164 | 38 | 0.6135 | 1.0198 | 0.4737 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 31 | 31 | 1.3635 | 2.2739 | 0.5484 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 29 | 29 | -0.1743 | -0.3874 | 0.5517 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 27 | 27 | -0.8735 | -1.2426 | 0.4444 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 71, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 868 | 867 | -0.586 | `keep_collecting` |
| `actual_order_submitted` | `false` | 905 | 751 | -0.6111 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 741 | 740 | -0.6243 | `keep_collecting` |
| `latency_state` | `simulated` | 741 | 740 | -0.6243 | `keep_collecting` |
| `actual_order_submitted` | `true` | 813 | 740 | -0.6243 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 730 | 729 | -0.6379 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 720 | 686 | -0.5191 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 670 | 670 | -0.5906 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 614 | 613 | -0.6785 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 632 | 612 | -0.6769 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 613 | 612 | -0.6769 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 480 | 479 | -0.5227 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 422 | 422 | -0.4415 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 364 | 364 | -0.5133 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 358 | 358 | -0.7452 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 306 | 305 | -0.9057 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 296 | 296 | -0.4603 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 233 | 233 | -0.8436 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 227 | 227 | -0.5723 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 128 | 128 | -0.3731 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 116 | 116 | -0.4234 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 71 | 70 | -0.9467 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 63 | 53 | -1.966 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 52 | 52 | -0.9542 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 49 | 49 | -0.3289 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 46 | 46 | -0.3602 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 28 | 28 | -0.5372 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -3.6922 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -1.9272 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 12 | 12 | -0.6201 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 11 | 11 | 0.2753 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 87 | 11 | 0.2753 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 11 | 11 | 0.2753 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 10 | 10 | 0.0252 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 9 | 9 | -0.9986 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 4 | 4 | -1.4313 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -3.5023 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -1.4313 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_lt1s` | 3 | 3 | -1.89 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | -1.0918 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 42, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 741 | 740 | -0.7359 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 741 | 740 | -0.7359 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 464 | 464 | -0.6627 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 471 | 462 | -1.527 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 280 | 280 | -1.4919 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 264 | 263 | -0.8883 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 172 | 172 | -1.6186 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 85 | 81 | 0.2134 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 88 | 77 | 0.7562 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 72 | 64 | -0.058 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 56 | 56 | 0.7777 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 49 | 49 | 0.2623 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 52 | 48 | 1.9562 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 44 | 44 | 0.0561 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 30 | 30 | 1.8399 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 30 | 30 | 0.0278 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.6988 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.3091 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 17 | 17 | 2.1414 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 13 | 13 | -0.2642 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -0.9327 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 17 | 8 | -0.5928 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.7605 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.3133 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.799 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.2951 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 45 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 38 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 45 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 81, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1281 | 1281 | -0.6439 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1281 | 1281 | -0.6439 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1281 | 1281 | -0.6439 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1103 | 1103 | -1.3315 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 712 | 712 | -0.7747 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 635 | 635 | -1.2004 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 485 | 485 | -0.4751 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 468 | 468 | -0.48 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 298 | 298 | -1.3571 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 236 | 236 | 0.5463 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 235 | 235 | -1.2614 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 231 | 231 | -0.0027 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 209 | 209 | -1.9003 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 183 | 183 | -0.8006 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 181 | 181 | 0.1566 | `hold_no_edge` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 137 | 137 | 0.6869 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 120 | 120 | 1.1985 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 115 | 115 | 0.4654 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 114 | 114 | 0.2837 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 101 | 101 | -2.5234 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 89 | 89 | -1.1163 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 85 | 85 | -1.7488 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 816 | 76 | 0.7472 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 70 | 70 | -1.1548 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 65 | 65 | 2.3659 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 60 | 60 | -0.8062 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 38 | 38 | -1.6179 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 32 | 32 | 0.1086 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 31 | 31 | 0.9477 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 31 | 31 | 0.8839 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 29 | 29 | -0.5477 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 28 | 28 | 1.145 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 26 | 26 | 2.2962 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 24 | 24 | -0.4145 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 21 | 21 | 1.4556 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 20 | 20 | 1.1248 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 17 | 17 | 0.4512 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 17 | 17 | 0.2248 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 16 | 16 | 2.8677 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 14 | 14 | -0.1917 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 294, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 81407 | 81351 | -0.7682 | -0.8282 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 64107 | 64107 | -0.243 | -0.2898 | 0.287 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 41572 | 41572 | -0.2077 | -0.2537 | 0.3077 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 37376 | 37334 | 0.9275 | 0.9147 | 0.9856 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20482 | 20482 | -0.0446 | -0.0268 | 0.352 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 9531 | 9531 | -0.3448 | -0.4126 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 9209 | 9209 | 0.6103 | 0.5561 | 0.9901 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 8385 | 8385 | -0.3022 | -0.3506 | 0.2679 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 7520 | 7520 | -0.2755 | -0.3111 | 0.2247 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 6522 | 6522 | -0.2754 | -0.3145 | 0.2327 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 3650 | 3650 | -0.3969 | -0.468 | 0.2513 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 2980 | 2980 | -0.2986 | -0.3507 | 0.252 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1727 | 1727 | -0.3806 | -0.4054 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 491 | 491 | 2.6555 | 2.6706 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 398 | 398 | -2.0115 | -2.5204 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 278 | 278 | -0.973 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 272 | 272 | -0.7622 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 270 | 270 | -0.0161 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 267 | 267 | -1.0724 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 263 | 263 | -0.8462 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 261 | 261 | -0.666 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 261 | 261 | -0.6887 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 236 | 236 | -0.7131 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 233 | 233 | -0.7315 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 227 | 227 | -0.0249 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 219 | 219 | -0.7576 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 212 | 212 | -0.9687 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 211 | 211 | -0.6703 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.32)` | 208 | 208 | -1.1813 | -1.32 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 206 | 206 | -0.2829 | -0.3123 | 0.199 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 203 | 203 | -0.9464 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 193 | 193 | -0.623 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.27)` | 191 | 191 | -1.1969 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 189 | 189 | -1.162 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 188 | 188 | -0.7207 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 188 | 188 | -0.8766 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 187 | 187 | -0.7956 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 184 | 184 | -0.8448 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 183 | 183 | -0.8736 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.23)` | 183 | 183 | -1.1126 | -1.23 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 166 | 121 | 0.6959 | 0.9278 | 0.5537 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 76 | 76 | 0.7472 | 0.9963 | 0.5658 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 121 | 76 | 0.7472 | 0.9963 | 0.5658 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 118 | 74 | 0.7721 | 1.0294 | 0.5811 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 90 | 45 | 0.6092 | 0.8122 | 0.5333 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 45 | 45 | 0.6092 | 0.8122 | 0.5333 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 76 | 38 | 0.738 | 0.9839 | 0.579 | `candidate_recovery_or_relax` |
| `overnight_action` | `action_unknown` | 31 | 31 | 0.9477 | 1.2635 | 0.6129 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_unknown` | 31 | 31 | 0.9477 | 1.2635 | 0.6129 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_unknown` | 31 | 31 | 0.9477 | 1.2635 | 0.6129 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_unknown` | 31 | 31 | 0.9477 | 1.2635 | 0.6129 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 31 | 31 | 0.9477 | 1.2635 | 0.6129 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 32 | 21 | 1.6697 | 2.2262 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 40 | 20 | -0.4492 | -0.599 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 23 | 14 | -0.7441 | -0.9921 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 23 | 14 | -0.2148 | -0.2864 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 11 | 11 | 1.663 | 2.2173 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_pos150_pos300` | 22 | 11 | 1.663 | 2.2173 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 19 | 11 | 0.1057 | 0.1409 | 0.5455 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300` | 10 | 10 | 1.677 | 2.236 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 8 | 3.4725 | 4.63 | 1.0 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 14 | 7 | -0.09 | -0.12 | 0.2857 | `hold_no_edge` |

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
