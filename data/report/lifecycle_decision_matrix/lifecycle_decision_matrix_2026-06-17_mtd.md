# Lifecycle Decision Matrix - 2026-06-17

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-17_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `188524`
- source_rows_total: `276383`
- retained_rows: `188524`
- dropped_rows_by_source: `{}`
- joined_rows: `172965`
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
- lifecycle_flow_bucket_count: `726`
- lifecycle_flow_complete_count: `889`
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
| `entry` | 9296 | 1369 | 0.6074 | 0.9732 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3566 | 2423 | -0.5452 | 0.9977 | `pass` | `NO_CHANGE` | False |
| `holding` | 3351 | 2423 | -0.9342 | 0.9974 | `pass` | `EXIT` | False |
| `scale_in` | 164482 | 162538 | -0.4295 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7829 | 4212 | -0.9591 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 726, 'complete_flow_count': 889, 'incomplete_flow_count': 171757, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 127269 | 126682 | -0.7282 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 35489 | 34132 | 0.6985 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1437 | 1437 | -1.0756 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 270 | 270 | 1.4611 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 235 | 235 | 1.5598 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 186 | 186 | 1.5434 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 118 | 118 | -0.2543 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 48 | 48 | -0.9294 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 30 | 30 | -0.907 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 28 | 28 | -0.8625 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 17 | 17 | -2.0005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 13 | 13 | -0.6042 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 13 | 13 | -0.8958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 11 | 11 | -0.8866 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 11 | 11 | -0.2686 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 10 | 10 | -1.1006 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 10 | 10 | -1.2681 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 442, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 6249 | 1363 | 0.6114 | 0.6858 | 0.4615 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 6012 | 1006 | 0.5258 | 0.2206 | 0.4433 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 695 | 695 | 1.5077 | 2.4469 | 0.6561 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 8622 | 695 | 1.5077 | 2.4469 | 0.6561 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 6629 | 629 | -0.3033 | -1.2122 | 0.2464 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 3954 | 504 | -0.1146 | -0.8386 | 0.2937 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3657 | 503 | -0.3295 | -1.2136 | 0.2465 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 4242 | 502 | -0.3293 | -1.2181 | 0.245 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1853 | 448 | 1.0252 | 1.7404 | 0.6228 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 448 | 448 | 1.0252 | 1.7404 | 0.6228 | `hold_sample` |
| `strength_bucket` | `strong_strength_momentum` | 850 | 402 | 0.8799 | 1.4525 | 0.5871 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 1778 | 347 | 0.3026 | 0.1763 | 0.4553 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 321 | 321 | -0.2296 | -1.9765 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 3652 | 311 | -0.3468 | -1.2893 | 0.2251 | `source_quality_workorder` |
| `score_band` | `score_70p` | 607 | 254 | 0.7634 | 1.4542 | 0.6102 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1333 | 222 | 0.4422 | 0.3525 | 0.4324 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 1375 | 176 | -0.0208 | -0.2569 | 0.3409 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 645 | 174 | 0.6083 | 0.906 | 0.4885 | `source_quality_workorder` |
| `score_band` | `score_66_69` | 324 | 174 | 0.973 | 1.4017 | 0.5747 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 170 | 170 | -0.5608 | 1.9553 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 99 | 99 | 1.0624 | 1.4389 | 0.6465 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 126, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3453 | 2423 | -0.5452 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3159 | 2423 | -0.5452 | `keep_collecting` |
| `latency_state` | `simulated` | 3159 | 2423 | -0.5452 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3443 | 2423 | -0.5452 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3118 | 2392 | -0.5298 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2899 | 2238 | -0.5693 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2581 | 1990 | -0.5655 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2543 | 1944 | -0.592 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1834 | 1401 | -0.6809 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1805 | 1397 | -0.5894 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1775 | 1385 | -0.692 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1661 | 1385 | -0.692 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1661 | 1385 | -0.692 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1614 | 1258 | -0.6239 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1466 | 1038 | -0.3493 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1466 | 1038 | -0.3493 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1345 | 1035 | -0.4237 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1186 | 837 | -0.3257 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1042 | 831 | -0.545 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1049 | 827 | -0.3824 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 598 | 448 | -0.2601 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 578 | 433 | -0.4519 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 260 | 185 | -0.2533 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 699 | 185 | -0.2533 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 260 | 185 | -0.2533 | `keep_collecting` |
| `would_limit_fill` | `false` | 666 | 184 | -0.255 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 197 | 128 | -0.762 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 57 | -0.5425 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 3159 | 2423 | -0.9342 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3159 | 2423 | -0.9342 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1876 | 1800 | -1.4302 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1881 | 1417 | -1.0316 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1062 | 1062 | -1.508 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1109 | 868 | -0.7549 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 620 | 620 | -1.2984 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 213 | 199 | 0.2302 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 162 | 156 | 0.5433 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 169 | 138 | -1.0609 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 167 | 127 | 0.0478 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 118 | 118 | -1.4219 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 116 | 116 | 0.1134 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 100 | 96 | 1.9889 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 87 | 87 | 0.0164 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 84 | 84 | 0.4385 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 81 | 81 | 0.3827 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 61 | 61 | 0.6442 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 47 | 47 | 2.0294 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 97 | 45 | -0.3715 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 43 | 43 | 1.9935 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 39 | 39 | 0.0868 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 24 | 24 | -0.4007 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 21 | 21 | -0.3381 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 1.6394 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 192 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 57 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 135 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 736 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 192 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 241 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 464 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 54 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 27 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3163 | 3163 | -1.3347 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2320 | 2320 | -0.9855 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1700 | 1700 | -1.0077 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1700 | 1700 | -1.0077 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1700 | 1700 | -1.0077 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1307 | 1307 | -1.207 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1035 | 1035 | -1.2924 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 885 | 885 | -1.4811 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 831 | 831 | -0.5229 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 662 | 662 | -1.7972 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 604 | 604 | -0.8956 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 529 | 529 | 0.5278 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 407 | 407 | -0.5093 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 364 | 364 | -1.7226 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 350 | 350 | -0.5431 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 348 | 348 | -1.1929 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 323 | 323 | -0.9148 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 292 | 292 | -1.2628 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 272 | 272 | -2.4068 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 206 | 206 | 0.2496 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3809 | 192 | -0.2117 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 192 | 192 | -0.2117 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 192 | 192 | -0.2117 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 172 | 172 | 0.0619 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 163 | 163 | 0.639 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 101 | 101 | 2.2052 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 98 | 98 | -1.6976 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 76 | 76 | -0.9739 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 75 | 75 | -0.3535 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 70 | 70 | 0.0738 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 58 | 58 | 1.0546 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 57 | 57 | 0.312 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 52 | 52 | -0.297 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 51 | 51 | 0.8126 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 46 | 46 | 2.3646 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 41 | 41 | -0.5096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 40 | 40 | 0.2655 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -0.4387 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 36 | 36 | 1.0296 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 667, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 162505 | 162505 | None | -0.4997 | 0.2066 | `hold_sample` |
| `arm` | `AVG_DOWN` | 128862 | 128275 | None | -0.8028 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 91282 | 91282 | None | -0.5004 | 0.2045 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 90284 | 89697 | None | -0.9651 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 38578 | 38578 | None | -0.4253 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 35620 | 34263 | None | 0.6363 | 0.9805 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 35620 | 34263 | None | 0.6363 | 0.9805 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 29920 | 29920 | None | -0.4579 | 0.2233 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 29057 | 29057 | None | 0.5207 | 0.9834 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 21900 | 21900 | None | -0.5199 | 0.2054 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 15673 | 15673 | None | -0.3286 | 0.161 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 10735 | 10735 | None | -0.5117 | 0.1939 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 8668 | 8668 | None | -0.5709 | 0.1892 | `hold_sample` |
| `blocker_reason` | `low_broken` | 3527 | 3527 | None | -0.4623 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1944 | 1944 | None | -0.8457 | 0.0792 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1401 | 1401 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1364 | 1364 | None | -2.3467 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1308 | 1308 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1266 | 1266 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1240 | 1240 | None | 3.2454 | 1.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 35, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 384 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 192 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 384 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 192 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 384 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 384 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 192 | 192 | -0.2117 | -0.2823 | 0.3125 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 270 | 135 | -0.195 | -0.2601 | 0.3259 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 264 | 132 | -0.6789 | -0.9052 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 76 | 76 | -0.9739 | -1.2986 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 152 | 76 | -0.9739 | -1.2986 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 114 | 57 | -0.2512 | -0.3349 | 0.2807 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 52 | 52 | -0.297 | -0.396 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 104 | 52 | -0.297 | -0.396 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 40 | 40 | 0.2655 | 0.354 | 0.9 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 80 | 40 | 0.2655 | 0.354 | 0.9 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 72 | 36 | 0.2994 | 0.3992 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 14 | 14 | 0.8657 | 1.1543 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 28 | 14 | 0.8657 | 1.1543 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 28 | 14 | 0.8657 | 1.1543 | 1.0 | `hold_sample` |

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
