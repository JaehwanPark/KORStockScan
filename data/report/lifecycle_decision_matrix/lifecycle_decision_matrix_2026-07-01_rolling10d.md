# Lifecycle Decision Matrix - 2026-07-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-01_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `52900`
- source_rows_total: `81990`
- retained_rows: `52900`
- dropped_rows_by_source: `{}`
- joined_rows: `31144`
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
- lifecycle_flow_bucket_count: `382`
- lifecycle_flow_complete_count: `262`
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
| `entry` | 4591 | 531 | 0.741 | 0.8007 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1077 | 550 | -0.5398 | 0.9687 | `pass` | `NO_CHANGE` | False |
| `holding` | 948 | 550 | -1.0299 | 0.9841 | `pass` | `EXIT` | False |
| `scale_in` | 29012 | 28392 | -0.523 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 17272 | 1121 | -0.916 | 0.817 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 382, 'complete_flow_count': 262, 'incomplete_flow_count': 46974, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 22196 | 22015 | -0.8757 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 6245 | 5806 | 0.8381 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 463 | 463 | -0.9828 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 165 | 165 | 1.1298 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 111 | 111 | 1.6812 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 55 | 55 | -0.0068 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 34 | 34 | 3.1224 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 16 | 16 | -0.8497 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 9 | 9 | -0.9944 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 8 | 8 | -0.625 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 7 | 7 | -1.349 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 6 | 6 | -1.8851 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 6 | 6 | -0.7393 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:f708d0f2a2` | 6 | 6 | 2.881 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:76e538b0ff` | 5 | 5 | -1.5047 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 4 | 4 | -1.8461 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 4 | 4 | -1.0246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 4 | 4 | -0.475 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 3 | 3 | -1.5619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:84461e0e65` | 3 | 3 | 2.7581 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 441, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 3357 | 524 | 0.7632 | 0.9467 | 0.4427 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 2880 | 392 | 0.6861 | 0.5607 | 0.4311 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 392 | 316 | 1.5107 | 2.4467 | 0.5886 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 4372 | 312 | 1.528 | 2.4754 | 0.5865 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 240 | 240 | 1.7 | 2.7222 | 0.6083 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2228 | 204 | -0.43 | -1.3554 | 0.2255 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 3366 | 190 | -0.4073 | -1.2986 | 0.2421 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 495 | 168 | 1.1026 | 1.6974 | 0.5417 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 683 | 163 | 1.7209 | 2.7499 | 0.6257 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 593 | 159 | 0.7601 | 1.0085 | 0.4843 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 1666 | 138 | 0.1446 | -0.614 | 0.2753 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1106 | 136 | 0.1214 | -0.4745 | 0.3309 | `hold_no_edge` |
| `score_band` | `score_60_62` | 2013 | 121 | -0.4799 | -1.5451 | 0.1901 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 105 | 105 | -0.2363 | -2.1271 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 860 | 103 | 1.18 | 1.2902 | 0.4758 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 720 | 94 | 0.237 | 0.7669 | 0.4468 | `hold_no_edge` |
| `score_band` | `score_66_69` | 221 | 93 | 1.6935 | 2.8856 | 0.6129 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_high` | 1295 | 91 | -0.5875 | -1.5861 | 0.2088 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 754 | 78 | -0.2563 | -1.3546 | 0.2051 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 488 | 67 | 0.8172 | 2.2829 | 0.5672 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 54 | 54 | -0.2915 | -3.418 | 0.0 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 50 | 50 | 1.0661 | 1.5295 | 0.56 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 38 | 38 | 0.865 | 1.0218 | 0.6316 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 143, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 949 | 550 | -0.5398 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 896 | 550 | -0.5398 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 896 | 550 | -0.5398 | `keep_collecting` |
| `latency_state` | `simulated` | 896 | 550 | -0.5398 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 949 | 550 | -0.5398 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 890 | 547 | -0.5338 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 805 | 491 | -0.5843 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 747 | 485 | -0.5598 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 716 | 467 | -0.5388 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 722 | 433 | -0.6085 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 617 | 408 | -0.5643 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 558 | 371 | -0.5647 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 526 | 294 | -0.4211 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 526 | 294 | -0.4211 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 386 | 253 | -0.6802 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 367 | 253 | -0.6802 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 367 | 253 | -0.6802 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 373 | 227 | -0.4141 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 264 | 158 | -0.2848 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 212 | 157 | -0.8391 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 174 | 114 | -0.2501 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 358 | 82 | -0.5095 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 140 | 78 | -0.6915 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 127 | 76 | -0.5504 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 175 | 68 | -0.3875 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 149 | 65 | -0.39 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 149 | 65 | -0.39 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 78 | 48 | -0.251 | `keep_collecting` |
| `would_limit_fill` | `true` | 74 | 35 | -0.2084 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 33 | -0.96 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 180 | 32 | -0.2813 | `keep_collecting` |
| `would_limit_fill` | `false` | 256 | 30 | -0.6019 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 29 | 25 | -0.1862 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 42 | 20 | 0.0517 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 40 | 20 | -0.7836 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 49, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 895 | 550 | -1.0299 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 895 | 550 | -1.0299 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 782 | 469 | -1.0406 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 420 | 401 | -1.5955 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 337 | 337 | -1.596 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 98 | 69 | -0.9566 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 54 | 54 | -1.5347 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 49 | 46 | 0.8942 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 41 | 41 | 0.8009 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 46 | 39 | 0.0638 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 37 | 37 | 0.0365 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 29 | 27 | 1.7765 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 40 | 24 | -0.5717 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 22 | 22 | -0.585 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 20 | 20 | 1.676 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 19 | 13 | -0.3482 | `hold_no_edge` |
| `holding_action` | `BUY` | 15 | 12 | -1.033 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 12 | 12 | -0.4214 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -1.9085 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.5512 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 5 | 5 | 1.6586 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 2 | 2 | 3.3445 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 2 | 2 | -0.425 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.53 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 53 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 5 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 10 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 36 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 345 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 53 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 313 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 29 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 66, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 795 | 795 | -1.3682 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 569 | 569 | -0.8543 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 569 | 569 | -0.8543 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 569 | 569 | -0.8543 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 499 | 499 | -1.0788 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 390 | 390 | -1.1711 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 215 | 215 | -1.2898 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 211 | 211 | -1.6269 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 172 | 172 | -1.9426 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 165 | 165 | -0.4308 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 161 | 161 | -0.5059 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 137 | 137 | -0.5049 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 123 | 123 | -1.0078 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 101 | 101 | -1.7584 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 89 | 89 | 0.9078 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 71 | 71 | -1.3955 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 62 | 62 | -2.6914 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 60 | 60 | -0.692 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 16204 | 53 | -0.0436 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 53 | 53 | -0.0436 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 53 | 53 | -0.0436 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 53 | 53 | -1.0977 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 47 | 47 | 0.9655 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 45 | 45 | 0.2903 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -1.7482 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 38 | 38 | 0.0034 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 35 | 35 | 2.3959 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 25 | 25 | 0.2028 | `hold_no_edge` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 19 | 19 | -0.4778 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 19 | 19 | -1.0307 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 17 | 17 | 1.8649 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 16 | 16 | 0.0362 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 15 | 15 | -0.2685 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 14 | 14 | -0.7419 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 13 | 13 | 0.8691 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 10 | 10 | 1.012 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 10 | 10 | 3.0919 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 9 | 9 | -0.9177 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 7 | 7 | 0.1778 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 7 | 7 | 0.7929 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 703, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 28374 | 28374 | None | -0.5841 | 0.1985 | `hold_sample` |
| `arm` | `AVG_DOWN` | 22703 | 22522 | None | -0.9405 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 18841 | 18660 | None | -1.0348 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 15993 | 15993 | None | -0.5476 | 0.2293 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 5996 | 5996 | None | -0.64 | 0.1629 | `hold_sample` |
| `arm` | `PYRAMID` | 6309 | 5870 | None | 0.7859 | 0.9613 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 6309 | 5870 | None | 0.7859 | 0.9613 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 4845 | 4845 | None | 0.5159 | 0.9744 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3862 | 3862 | None | -0.4848 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 3053 | 3053 | None | -0.6719 | 0.1382 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 1769 | 1769 | None | -0.6102 | 0.1543 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1563 | 1563 | None | -0.5427 | 0.1868 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 918 | 918 | None | -0.5611 | 0.0632 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 661 | 661 | None | -0.8389 | 0.1074 | `hold_sample` |
| `blocker_reason` | `low_broken` | 495 | 495 | None | -0.4606 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 451 | 451 | None | 3.133 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `scalping_buy_window_blocked` | 374 | 374 | None | -0.4856 | 0.0829 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 106 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 53 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 106 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 53 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 106 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 53 | 53 | -0.0436 | -0.0581 | 0.3208 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 100 | 50 | -0.0359 | -0.0478 | 0.34 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 72 | 36 | 0.2208 | 0.2945 | 0.3889 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 72 | 36 | -0.6594 | -0.8792 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 19 | 19 | -1.0307 | -1.3742 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 38 | 19 | -1.0307 | -1.3742 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 16 | 16 | -0.2564 | -0.3419 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 32 | 16 | -0.2564 | -0.3419 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 20 | 10 | -0.657 | -0.876 | 0.3 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 7 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 14 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 14 | 7 | 0.7929 | 1.0571 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 6 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 12 | 6 | 0.22 | 0.2933 | 0.8333 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 10 | 5 | -0.525 | -0.7 | 0.0 | `hold_sample` |

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
