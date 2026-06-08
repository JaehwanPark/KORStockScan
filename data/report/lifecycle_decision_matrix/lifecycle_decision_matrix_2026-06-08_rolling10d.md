# Lifecycle Decision Matrix - 2026-06-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-08_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `40756`
- source_rows_total: `71818`
- retained_rows: `40756`
- dropped_rows_by_source: `{}`
- joined_rows: `39039`
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
- lifecycle_flow_bucket_count: `217`
- lifecycle_flow_complete_count: `139`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0036`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1301 | 261 | 0.5989 | 0.9849 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 622 | 538 | -0.4543 | 0.9894 | `pass` | `NO_CHANGE` | False |
| `holding` | 580 | 538 | -0.9655 | 0.9881 | `pass` | `EXIT` | False |
| `scale_in` | 36487 | 36485 | -0.4012 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1766 | 1217 | -0.9911 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 217, 'complete_flow_count': 139, 'incomplete_flow_count': 37948, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 27666 | 27664 | -0.7236 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 8342 | 8342 | 0.6942 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 398 | 398 | -1.1353 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 62 | 62 | 1.2932 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 56 | 56 | 0.3133 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 49 | 49 | 1.1284 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 40 | 40 | -0.553 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 13 | 13 | -0.9823 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 10 | 10 | -0.796 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:23320ac43e` | 5 | 5 | -0.1805 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:ffa670224b` | 5 | 5 | 1.0715 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 5 | 5 | -0.309 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 5 | 5 | 2.2264 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:0562f02c36` | 4 | 4 | -0.8877 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:50092e1a75` | 4 | 4 | -0.8943 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 257, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 167 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1207 | 167 | 0.9163 | 1.5581 | 0.6527 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 673 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 167 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 167 | 167 | 0.9163 | 1.5581 | 0.6527 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 174 | 123 | 0.898 | 1.5176 | 0.6423 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 399 | 101 | 0.6349 | 0.7433 | 0.6336 | `source_quality_workorder` |
| `strength_bucket` | `risk_unknown` | 396 | 94 | 0.0352 | -1.0288 | 0.2766 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 396 | 94 | 0.0352 | -1.0288 | 0.2766 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 610 | 93 | 0.0141 | -1.0173 | 0.2796 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 539 | 92 | 0.0528 | -1.0085 | 0.2826 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 211 | 91 | 0.4694 | 0.3336 | 0.6593 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 424 | 85 | 0.0449 | -1.0105 | 0.2823 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 330 | 83 | 0.1655 | -0.8456 | 0.3132 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 269 | 68 | 1.0944 | 1.2719 | 0.5 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 130 | 66 | 1.1687 | 1.647 | 0.6212 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 622 | 61 | 0.0052 | -0.8339 | 0.2951 | `source_quality_workorder` |
| `score_band` | `score_70p` | 130 | 60 | 0.3217 | 0.8706 | 0.5833 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 357 | 53 | 0.2457 | 0.5184 | 0.4528 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 52 | 52 | -0.044 | -1.9323 | 0.0 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 22 | 22 | 0.257 | -0.3105 | 0.7273 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 76, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 718 | 718 | -0.355 | `keep_collecting` |
| `actual_order_submitted` | `false` | 745 | 571 | -0.4379 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 538 | 538 | -0.4543 | `keep_collecting` |
| `latency_state` | `simulated` | 538 | 538 | -0.4543 | `keep_collecting` |
| `actual_order_submitted` | `true` | 616 | 538 | -0.4543 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 505 | 505 | -0.4728 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 435 | 428 | -0.457 | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 427 | 427 | -0.3766 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 358 | 358 | -0.6533 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 371 | 351 | -0.627 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 351 | 351 | -0.627 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 338 | 338 | -0.4795 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 302 | 302 | -0.4381 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 261 | 261 | -0.5252 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 241 | 241 | -0.4209 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 215 | 215 | -0.4804 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 187 | 187 | -0.1299 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 165 | 165 | -0.4871 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 152 | 152 | -0.0672 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 152 | 152 | -0.5492 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 111 | 111 | -0.7528 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 104 | 104 | -0.4169 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 103 | 103 | -0.3401 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 81 | 81 | -0.0838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 63 | 63 | -0.0807 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 56 | 56 | -0.3992 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 33 | 33 | -0.1712 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 117 | 33 | -0.1712 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 33 | 33 | -0.1712 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 29 | 29 | -0.1613 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 21 | 21 | -0.4183 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 21 | 21 | -2.6509 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -0.4111 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 7 | 7 | -1.9723 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | 0.3767 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -1.3182 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 4 | 4 | -0.2428 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 3 | 3 | -0.0727 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 3 | 3 | -0.0727 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 2 | 2 | 1.8438 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 538 | 538 | -0.9655 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 538 | 538 | -0.9655 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 422 | 403 | -1.4951 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 320 | 320 | -1.0252 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 239 | 239 | -1.6112 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 171 | 171 | -0.932 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 126 | 126 | -1.3851 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 47 | 47 | -0.6816 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 44 | 43 | 0.2192 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 38 | 38 | -1.1288 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 38 | 34 | 0.2907 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 33 | 33 | 0.6255 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 27 | 27 | -0.0361 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 21 | 21 | 0.3912 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 20 | 20 | 0.5283 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 22 | 19 | 2.382 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 15 | 15 | 0.5681 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 13 | 13 | 0.1283 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 3.2883 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.478 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 21 | 6 | -0.36 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.2501 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 5 | 5 | -0.386 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 4 | 4 | 0.7673 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 0.9097 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.23 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 42 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 26 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 42 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos150_pos300_plus|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 58, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 916 | 916 | -1.3777 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 708 | 708 | -0.9836 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 467 | 467 | -1.07 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 467 | 467 | -1.07 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 467 | 467 | -1.07 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 366 | 366 | -1.2446 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 307 | 307 | -1.2559 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 280 | 280 | -0.4621 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 270 | 270 | -1.628 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 220 | 220 | -1.8253 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 177 | 177 | 0.5288 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 158 | 158 | -0.8066 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 113 | 113 | -0.8536 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 108 | 108 | -0.5111 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 105 | 105 | -1.7756 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 102 | 102 | -1.157 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 93 | 93 | -0.5455 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 89 | 89 | -2.6318 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 89 | 89 | -1.1536 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 84 | 84 | -0.2409 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 66 | 66 | 0.1888 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 56 | 56 | 0.1572 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 46 | 46 | 0.6577 | `candidate_recovery_or_relax` |
| `exit_outcome` | `outcome_unknown` | 591 | 42 | -0.2409 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 33 | 33 | -0.4066 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 29 | 29 | -1.701 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 25 | 25 | 2.3777 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 21 | 21 | 1.1708 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 19 | 19 | -0.8657 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 17 | 17 | 0.7592 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 17 | 17 | 0.5308 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 16 | 16 | -0.4327 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 16 | 16 | -0.3063 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 15 | 15 | -0.298 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 15 | 15 | 1.054 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 13 | 13 | 0.0145 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 11 | 11 | 2.8883 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 9 | 9 | 0.9873 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 8 | 8 | 1.0936 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 6 | 6 | 0.2633 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 373, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 47969 | 47965 | -0.7915 | -0.8805 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 36485 | 36485 | -0.4012 | -0.4904 | 0.2268 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 17822 | 17822 | -0.4088 | -0.5077 | 0.206 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 16768 | 16768 | 0.6928 | 0.5956 | 0.9872 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 9238 | 9238 | -0.3437 | -0.4323 | 0.2598 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 8237 | 8237 | -0.3547 | -0.429 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 7669 | 7669 | 0.6708 | 0.5674 | 0.9885 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_60_62` | 5313 | 5313 | -0.443 | -0.5068 | 0.2799 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 3126 | 3126 | -0.3074 | -0.3248 | 0.1612 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 2854 | 2854 | -0.4094 | -0.4861 | 0.1846 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 1258 | 1258 | -0.5189 | -0.6107 | 0.1518 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 719 | 719 | -0.853 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 691 | 691 | -0.4113 | -0.4366 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 607 | 607 | -1.0279 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 603 | 603 | -0.7222 | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 585 | 585 | -0.646 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 579 | 579 | -1.2545 | -1.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 557 | 557 | -0.9353 | -0.9353 | 0.0915 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 512 | 512 | -1.2556 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 487 | 487 | -0.9267 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 479 | 479 | -1.0205 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 363 | 363 | -0.4417 | -0.4776 | 0.1047 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 325 | 325 | -1.949 | -2.4334 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 268 | 268 | -0.791 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 222 | 222 | -0.6818 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 217 | 217 | -1.0187 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 214 | 214 | -0.6405 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 213 | 213 | -0.7132 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.02)` | 210 | 210 | -0.9346 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 208 | 208 | -0.7293 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 206 | 206 | -0.8445 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 206 | 206 | -0.9659 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 192 | 192 | -0.8526 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 191 | 191 | -0.9272 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 184 | 184 | -0.6973 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 181 | 181 | -0.8458 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 181 | 181 | -0.9582 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 177 | 177 | -1.0423 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 171 | 171 | -0.9114 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 168 | 168 | -0.803 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 30, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 126 | 84 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 84 | 42 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 42 | 42 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 84 | 42 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 84 | 42 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 42 | 42 | -0.2409 | -0.3212 | 0.1905 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 68 | 34 | -0.6152 | -0.8203 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 52 | 26 | -0.1073 | -0.1431 | 0.1923 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 19 | 19 | -0.8657 | -1.1542 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 38 | 19 | -0.8657 | -1.1542 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 32 | 16 | -0.4579 | -0.6106 | 0.1875 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 15 | 15 | -0.298 | -0.3973 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 30 | 15 | -0.298 | -0.3973 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 4 | 4 | 0.2625 | 0.35 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 8 | 4 | 0.2625 | 0.35 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 4 | 0.2625 | 0.35 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 3 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos150_pos300_plus` | 6 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 6 | 3 | 2.9025 | 3.87 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 1 | 1 | 1.0425 | 1.39 | 1.0 | `hold_sample` |

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
