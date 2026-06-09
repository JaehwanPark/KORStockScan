# Lifecycle Decision Matrix - 2026-06-09

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-09_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `61618`
- source_rows_total: `108163`
- retained_rows: `61618`
- dropped_rows_by_source: `{}`
- joined_rows: `58364`
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
- lifecycle_flow_bucket_count: `309`
- lifecycle_flow_complete_count: `276`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0048`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2730 | 462 | 0.9049 | 0.9915 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 924 | 819 | -0.4611 | 0.9931 | `pass` | `NO_CHANGE` | False |
| `holding` | 877 | 819 | -0.9177 | 0.9922 | `pass` | `EXIT` | False |
| `scale_in` | 54541 | 54538 | -0.3706 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2546 | 1726 | -0.9704 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 309, 'complete_flow_count': 276, 'incomplete_flow_count': 56755, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 40242 | 40239 | -0.7146 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 13593 | 13593 | 0.6742 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 600 | 600 | -1.1222 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 122 | 122 | 1.5045 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 80 | 80 | 1.817 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 79 | 79 | 1.5258 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 50 | 50 | -0.4894 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 20 | 20 | -0.9305 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 13 | 13 | -0.8077 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 6 | 6 | -1.771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:23320ac43e` | 5 | 5 | -0.1805 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ffa670224b` | 5 | 5 | 1.0715 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c6e869aefc` | 5 | 5 | -0.9751 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 5 | 5 | -0.73 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 5 | 5 | -0.309 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 320, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1539 | 460 | 0.9122 | 1.242 | 0.5304 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 1354 | 303 | 0.6922 | 0.5331 | 0.5082 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 281 | 281 | 1.5995 | 2.6369 | 0.6797 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 2549 | 281 | 1.5995 | 2.6369 | 0.6797 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 673 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 167 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 1615 | 164 | -0.148 | -1.0374 | 0.2683 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 184 | 129 | 0.8494 | 1.4628 | 0.6434 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 483 | 119 | 0.3704 | -0.2043 | 0.395 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 399 | 101 | 0.6349 | 0.7433 | 0.6336 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 396 | 94 | 0.0352 | -1.0288 | 0.2766 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 496 | 93 | 0.04 | -1.0512 | 0.2688 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 85 | 85 | -0.2101 | -1.979 | 0.0 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 206 | 75 | 1.5802 | 3.4892 | 0.6267 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 269 | 68 | 1.0944 | 1.2719 | 0.5 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 334 | 67 | 0.8406 | 0.9577 | 0.4776 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 130 | 66 | 1.1687 | 1.647 | 0.6212 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 622 | 61 | 0.0052 | -0.8339 | 0.2951 | `source_quality_workorder` |
| `score_band` | `score_70p` | 130 | 60 | 0.3217 | 0.8706 | 0.5833 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 357 | 53 | 0.2457 | 0.5184 | 0.4528 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 52 | 52 | -0.1917 | 1.856 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 35 | 35 | 0.8978 | 1.0387 | 0.7143 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 77, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1103 | 1103 | -0.3782 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1076 | 860 | -0.4433 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 819 | 819 | -0.4611 | `keep_collecting` |
| `latency_state` | `simulated` | 819 | 819 | -0.4611 | `keep_collecting` |
| `actual_order_submitted` | `true` | 918 | 819 | -0.4611 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 778 | 778 | -0.4807 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 679 | 679 | -0.4184 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 681 | 672 | -0.4692 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 535 | 535 | -0.6319 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 553 | 525 | -0.6068 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 525 | 525 | -0.6068 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 449 | 449 | -0.5202 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 425 | 425 | -0.4049 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 405 | 405 | -0.4407 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 374 | 374 | -0.4419 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 350 | 350 | -0.5762 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 326 | 326 | -0.4416 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 294 | 294 | -0.2007 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 268 | 268 | -0.5252 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 250 | 250 | -0.1723 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 146 | 146 | -0.1385 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 140 | 140 | -0.6678 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 137 | 137 | -0.3128 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 133 | 133 | -0.5249 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 94 | 94 | -0.2582 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 73 | 73 | -0.3708 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 41 | 41 | -0.0893 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 146 | 41 | -0.0893 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 41 | 41 | -0.0893 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 40 | 40 | -0.847 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 37 | 37 | -0.0727 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 24 | 24 | -2.4602 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -0.7721 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 10 | 10 | -1.9472 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | 0.2339 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -0.6715 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 4 | 4 | -0.2428 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 3 | 3 | 1.1932 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 3 | 3 | -0.0727 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 3 | 3 | -4.0909 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 819 | 819 | -0.9177 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 819 | 819 | -0.9177 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 631 | 604 | -1.4196 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 421 | 421 | -0.9784 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 343 | 343 | -0.861 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 304 | 304 | -1.5663 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 254 | 254 | -1.2835 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 76 | 73 | 0.205 | `hold_sample` |
| `holding_action` | `BUY` | 55 | 55 | -0.8077 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 60 | 54 | 0.1455 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 47 | 46 | 0.5481 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 46 | 46 | -1.2018 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 40 | 40 | 0.015 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 32 | 32 | 0.3902 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 31 | 31 | 0.1865 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 32 | 29 | 2.1286 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 27 | 27 | 0.516 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 23 | 23 | 0.0902 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 15 | 15 | 2.9867 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 14 | 14 | 0.3592 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 31 | 13 | -0.3045 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 11 | 11 | 1.2909 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.3452 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.2501 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 0.9097 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 58 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 22 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 58 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 17 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 65, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1296 | 1296 | -1.3385 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 973 | 973 | -0.9477 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 695 | 695 | -1.0616 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 695 | 695 | -1.0616 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 695 | 695 | -1.0616 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 545 | 545 | -1.2397 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 397 | 397 | -1.276 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 386 | 386 | -0.4691 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 357 | 357 | -1.5485 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 292 | 292 | -1.7562 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 244 | 244 | 0.4706 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 230 | 230 | -0.8185 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 158 | 158 | -0.5111 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 149 | 149 | -0.8716 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 136 | 136 | -0.5496 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 136 | 136 | -1.1552 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 131 | 131 | -1.7771 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 117 | 117 | -2.4842 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 117 | 117 | -1.2301 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 116 | 116 | -0.2573 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 97 | 97 | 0.1911 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 80 | 80 | 0.1016 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 59 | 59 | 0.5838 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 878 | 58 | -0.2573 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 43 | 43 | -0.3885 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.6677 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 38 | 38 | -0.4259 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 36 | 36 | 2.2079 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 27 | 27 | -0.8628 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 25 | 25 | 0.5591 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 25 | 25 | 1.0762 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 25 | 25 | 0.4437 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 24 | 24 | 0.8745 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 20 | 20 | -0.4427 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 20 | 20 | -0.2449 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 19 | 19 | -0.0632 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 18 | 18 | -0.2934 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 16 | 16 | 2.711 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -0.4831 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 13 | 13 | 0.9109 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 427, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 69823 | 69817 | -0.7813 | -0.865 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 54538 | 54538 | -0.3706 | -0.4519 | 0.2453 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 28485 | 28485 | -0.3636 | -0.4493 | 0.2423 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 27290 | 27290 | 0.6733 | 0.5931 | 0.9806 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 12200 | 12200 | 0.6573 | 0.5722 | 0.9851 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 11969 | 11969 | -0.3551 | -0.4253 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 11792 | 11792 | -0.3322 | -0.4164 | 0.2643 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 6827 | 6827 | -0.4436 | -0.5072 | 0.2635 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 5516 | 5516 | -0.28 | -0.2985 | 0.1896 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 4069 | 4069 | -0.3651 | -0.4387 | 0.215 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 3365 | 3365 | -0.4233 | -0.5032 | 0.2042 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1043 | 1043 | -0.4284 | -0.4542 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 802 | 802 | -0.9336 | -0.9336 | 0.0785 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 745 | 745 | -0.8533 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 678 | 678 | -1.0356 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 647 | 647 | -0.7177 | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 626 | 626 | -0.6536 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 614 | 614 | -1.2548 | -1.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 602 | 602 | -0.9238 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 555 | 555 | -1.2595 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 519 | 519 | -1.0176 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 460 | 460 | -1.9258 | -2.4065 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 432 | 432 | -0.8627 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 423 | 423 | -0.4449 | -0.4814 | 0.0993 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 363 | 363 | -0.6528 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 363 | 363 | -0.7903 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 355 | 355 | -1.0983 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 337 | 337 | -0.9355 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 335 | 335 | -0.8508 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 322 | 322 | -0.6768 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 293 | 293 | -0.7175 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 286 | 286 | -0.9195 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 283 | 283 | -0.6894 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 274 | 274 | -0.8516 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 270 | 270 | -1.1736 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 267 | 267 | -0.7322 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 262 | 262 | -1.0473 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 259 | 259 | -1.0215 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 257 | 257 | -0.9548 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 257 | 257 | -0.9625 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 174 | 116 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 116 | 58 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 58 | 58 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 116 | 58 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 116 | 58 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 58 | 58 | -0.2573 | -0.3431 | 0.2069 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 92 | 46 | -0.6228 | -0.8304 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 72 | 36 | -0.1477 | -0.1969 | 0.2222 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 27 | 27 | -0.8628 | -1.1504 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 54 | 27 | -0.8628 | -1.1504 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 44 | 22 | -0.4367 | -0.5823 | 0.1818 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 18 | 18 | -0.2934 | -0.3911 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 36 | 18 | -0.2934 | -0.3911 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.2025 | 0.27 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.2025 | 0.27 | 0.8333 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.258 | 0.344 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 3 | 3 | 0.8625 | 1.15 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 3 | 0.8625 | 1.15 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 6 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |

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
