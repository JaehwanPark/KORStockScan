# Lifecycle Decision Matrix - 2026-06-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-22_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `29342`
- source_rows_total: `47327`
- retained_rows: `29342`
- dropped_rows_by_source: `{}`
- joined_rows: `25202`
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
- lifecycle_flow_bucket_count: `313`
- lifecycle_flow_complete_count: `224`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0087`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2714 | 285 | 1.2283 | 0.9001 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 704 | 400 | -0.1873 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 672 | 400 | -0.8117 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 23516 | 23300 | -0.4513 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1736 | 817 | -0.8046 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 313, 'complete_flow_count': 224, 'incomplete_flow_count': 25518, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 18362 | 18288 | -0.7219 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 4729 | 4587 | 0.6466 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 331 | 331 | -0.9447 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 106 | 106 | 1.8027 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 63 | 63 | 1.7693 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 32 | 32 | -0.0697 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 19 | 19 | 1.6224 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 14 | 14 | -0.9486 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 13 | 13 | -0.5353 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -0.6367 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:02eec4d554` | 4 | 4 | -1.2391 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:2b39f2b635` | 4 | 4 | -1.3141 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 4 | 4 | -1.2414 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:23495871ee` | 3 | 3 | -1.9545 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:d10e0f64d0` | 3 | 3 | -3.6057 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:00638643f7` | 3 | 3 | -0.9439 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 3 | 3 | -2.143 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 3 | 3 | 0.584 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:be3bcb1776` | 3 | 3 | -2.0044 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 3 | 3 | -1.4394 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 329, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1940 | 282 | 1.2148 | 1.2688 | 0.5071 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1912 | 236 | 0.8286 | 0.4222 | 0.4661 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 191 | 191 | 1.7848 | 2.7004 | 0.6649 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2620 | 191 | 1.7848 | 2.7004 | 0.6649 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 647 | 191 | 1.7848 | 2.7004 | 0.6649 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 191 | 191 | 1.7848 | 2.7004 | 0.6649 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 369 | 179 | 1.5969 | 2.2334 | 0.6145 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 468 | 142 | 1.4309 | 1.8525 | 0.5422 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 926 | 131 | 1.6363 | 2.2151 | 0.6107 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1718 | 97 | 0.6496 | -0.2392 | 0.3196 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 628 | 96 | 0.7834 | 0.6602 | 0.4479 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1510 | 94 | 0.0977 | -1.5371 | 0.1915 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 1967 | 73 | 0.1529 | -1.576 | 0.2192 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 1063 | 67 | 0.1062 | -1.2012 | 0.2388 | `hold_no_edge` |
| `score_band` | `score_66_69` | 145 | 67 | 1.6277 | 2.4455 | 0.6567 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 53 | 53 | 1.384 | 2.0777 | 0.6415 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1552 | 48 | 0.0985 | -1.7317 | 0.1875 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 42 | 42 | 0.0469 | -2.0164 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 34 | 34 | 0.3533 | -3.1015 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 32 | 32 | 1.5703 | 2.1465 | 0.7188 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 195 | 25 | 1.2765 | 1.2059 | 0.56 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 94 | 22 | 5.2455 | 8.9694 | 0.6818 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 76 | 21 | -0.0944 | -1.4019 | 0.0952 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 108 | 15 | 0.5485 | -1.5047 | 0.2667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 11 | 11 | 1.0851 | 1.1037 | 0.5455 | `candidate_recovery_or_relax` |

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
| `actual_order_submitted` | `false` | 683 | 400 | -0.1873 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 607 | 400 | -0.1873 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 607 | 400 | -0.1873 | `keep_collecting` |
| `latency_state` | `simulated` | 607 | 400 | -0.1873 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 676 | 400 | -0.1873 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 603 | 397 | -0.1815 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 581 | 388 | -0.1835 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 562 | 371 | -0.1371 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 511 | 330 | -0.1787 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 468 | 303 | -0.0945 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 442 | 287 | -0.0765 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 422 | 283 | -0.182 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 332 | 226 | -0.3423 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 303 | 226 | -0.3423 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 303 | 226 | -0.3423 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 302 | 172 | 0.0171 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 302 | 172 | 0.0171 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 275 | 159 | 0.0411 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 188 | 144 | -0.4525 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 201 | 110 | 0.1569 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 135 | 99 | -0.5034 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 120 | 86 | -0.4967 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 94 | 67 | -0.1952 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 126 | 57 | -0.4822 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 75 | 46 | 0.181 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 142 | 29 | -0.8302 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 35 | 27 | 0.5198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 28 | 20 | -0.2307 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 20 | 17 | 0.1025 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 30 | 16 | -0.185 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 69 | 14 | -0.3051 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 123 | 12 | -0.3113 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 26 | 12 | -0.3113 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 26 | 12 | -0.3113 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 14 | 12 | -0.4712 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 606 | 400 | -0.8117 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 606 | 400 | -0.8117 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 314 | 295 | -1.4175 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 419 | 263 | -0.7583 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 191 | 191 | -1.4415 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 155 | 109 | -0.8579 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 80 | 80 | -1.3695 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 35 | 29 | 1.1712 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 32 | 28 | -1.133 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 32 | 25 | 0.3349 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 24 | 24 | -1.3866 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 39 | 21 | 0.1869 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 1.3062 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 21 | 18 | 2.8493 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 17 | 17 | 0.4369 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 25 | 12 | -0.3383 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | 0.2059 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 12 | 12 | 3.5217 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.37 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 8 | 8 | 0.11 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 8 | 8 | 0.8167 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 6 | 6 | -0.0418 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.8486 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.18 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | -0.2155 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 66 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 54 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 206 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 66 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 156 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 46 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 15 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 561 | 561 | -1.2976 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 413 | 413 | -0.8078 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 413 | 413 | -0.8078 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 413 | 413 | -0.8078 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 338 | 338 | -1.0093 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 264 | 264 | -1.1868 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 142 | 142 | -1.1593 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 136 | 136 | -1.711 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 135 | 135 | -0.4854 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 125 | 125 | -1.3869 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 123 | 123 | -0.508 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 117 | 117 | -0.5816 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 96 | 96 | -1.0387 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 985 | 66 | 0.2639 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 66 | 66 | 0.2639 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 66 | 66 | 0.2639 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 60 | 60 | 0.9364 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 60 | 60 | -1.1731 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 59 | 59 | -1.1256 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 47 | 47 | -1.4978 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 46 | 46 | -2.5185 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 36 | 36 | -0.7725 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 33 | 33 | 0.1943 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 33 | 33 | 1.1646 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 31 | 31 | 0.4043 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 30 | 30 | -1.5488 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 24 | 24 | 3.2808 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 19 | 19 | -0.911 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 19 | 19 | 0.1393 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 12 | 12 | -0.2538 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 12 | 12 | 0.5202 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 11 | 11 | 0.2436 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 10 | 10 | -0.3247 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 10 | 10 | 1.448 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 9 | 9 | 1.1022 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 7 | 7 | 0.8261 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos150_pos300` | 6 | 6 | 1.5112 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 6 | 6 | 1.015 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300_plus` | 5 | 5 | 5.1794 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 5 | 5 | 0.5643 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 373, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 23294 | 23294 | None | -0.5027 | 0.1905 | `hold_sample` |
| `arm` | `AVG_DOWN` | 18739 | 18665 | None | -0.7757 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 14728 | 14728 | None | -0.5253 | 0.1795 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 12730 | 12656 | None | -0.9469 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 6009 | 6009 | None | -0.4152 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 4777 | 4635 | None | 0.5966 | 0.9581 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 4777 | 4635 | None | 0.5966 | 0.9581 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 4420 | 4420 | None | -0.516 | 0.1715 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 3702 | 3702 | None | 0.4836 | 0.967 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 2807 | 2807 | None | -0.3131 | 0.1657 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 2218 | 2218 | None | -0.4197 | 0.2521 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1150 | 1150 | None | -0.4294 | 0.2079 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 778 | 778 | None | -0.3441 | 0.3059 | `hold_sample` |
| `blocker_reason` | `low_broken` | 577 | 577 | None | -0.447 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 523 | 523 | None | -0.7674 | 0.1205 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 281 | 281 | None | -1.09 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 250 | 250 | None | -2.5617 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_cutoff` | 189 | 189 | None | -0.1659 | 0.2381 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.91)` | 178 | 178 | None | -0.91 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.25)` | 175 | 175 | None | -1.25 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 132 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 66 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 132 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `stage` | `exit` | 66 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 132 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 66 | 66 | 0.2639 | 0.352 | 0.4545 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 128 | 64 | 0.2776 | 0.3701 | 0.4687 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 108 | 54 | 0.3903 | 0.5204 | 0.5 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 72 | 36 | -0.5731 | -0.7642 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 19 | 19 | -0.911 | -1.2147 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 38 | 19 | -0.911 | -1.2147 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 18 | 18 | 0.1512 | 0.2017 | 0.7778 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 36 | 18 | 0.1512 | 0.2017 | 0.7778 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 28 | 14 | 0.2089 | 0.2786 | 1.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 13 | 13 | -0.24 | -0.32 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 26 | 13 | -0.24 | -0.32 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 24 | 12 | -0.3044 | -0.4059 | 0.25 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 7 | 7 | 0.8261 | 1.1014 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 14 | 7 | 0.8261 | 1.1014 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 7 | 0.8261 | 1.1014 | 1.0 | `hold_sample` |

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
