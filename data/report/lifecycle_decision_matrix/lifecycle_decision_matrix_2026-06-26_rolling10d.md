# Lifecycle Decision Matrix - 2026-06-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-26_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `80203`
- source_rows_total: `105474`
- retained_rows: `80203`
- dropped_rows_by_source: `{}`
- joined_rows: `63408`
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
- lifecycle_flow_bucket_count: `512`
- lifecycle_flow_complete_count: `510`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0071`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 6807 | 736 | 0.9147 | 0.9024 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1459 | 930 | -0.4232 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1390 | 930 | -0.9562 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 60187 | 59061 | -0.4025 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 10360 | 1751 | -0.8918 | 0.9715 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 512, 'complete_flow_count': 510, 'incomplete_flow_count': 71105, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 45914 | 45654 | -0.7136 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 13470 | 12604 | 0.745 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 648 | 648 | -0.972 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 199 | 199 | 1.4944 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 163 | 163 | 1.9907 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 67 | 67 | -0.1589 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 56 | 56 | 2.2785 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 20 | 20 | -0.915 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 15 | 15 | -0.6066 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 14 | 14 | -0.8718 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 12 | 12 | -2.01 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 9 | 9 | -1.0434 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:c1801bf4e3` | 9 | 9 | -1.715 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 9 | 9 | -0.6856 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 9 | 9 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 8 | 8 | -1.2981 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 7 | 7 | -0.7726 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 7 | 7 | -1.3363 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1b4e4b3128` | 6 | 6 | -2.6958 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 6 | 6 | -0.5657 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 441, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5044 | 729 | 0.9135 | 0.9605 | 0.4513 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 4952 | 599 | 0.7748 | 0.4901 | 0.4307 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 425 | 425 | 1.7805 | 2.7416 | 0.64 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 6496 | 425 | 1.7805 | 2.7416 | 0.64 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 425 | 425 | 1.7805 | 2.7416 | 0.64 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 1120 | 348 | 1.8081 | 2.7589 | 0.6552 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 893 | 333 | 1.4558 | 2.0787 | 0.5916 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4208 | 311 | -0.2686 | -1.4556 | 0.1929 | `hold_no_edge` |
| `chosen_action` | `NO_BUY_AI` | 5294 | 268 | -0.2996 | -1.4813 | 0.1978 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 3976 | 268 | 0.2979 | -0.4943 | 0.2873 | `hold_no_edge` |
| `score_band` | `score_70p` | 827 | 266 | 1.1027 | 1.4668 | 0.5263 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1364 | 194 | 1.4612 | 1.9132 | 0.5464 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 2885 | 187 | -0.142 | -1.3362 | 0.2139 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1319 | 181 | 0.4355 | -0.0532 | 0.3425 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 3963 | 176 | -0.2913 | -1.7107 | 0.1591 | `hold_no_edge` |
| `score_band` | `score_66_69` | 390 | 176 | 1.8459 | 2.8011 | 0.625 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 154 | 154 | -0.2238 | -1.9744 | 0.0 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 777 | 101 | 0.4525 | 1.3664 | 0.5149 | `hold_sample` |
| `exit_rule` | `scalp_hard_stop_pct` | 94 | 94 | -0.0745 | -3.1696 | 0.0 | `hold_no_edge` |
| `stale_bucket` | `stale_high` | 1655 | 94 | -0.4964 | -1.8491 | 0.1383 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 88 | 88 | 1.4851 | 2.2561 | 0.6705 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 594 | 87 | 1.295 | 1.9251 | 0.5172 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 71 | 71 | 1.7834 | 2.5449 | 0.7042 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 54 | 54 | -0.4149 | 2.4828 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 353 | 47 | 0.4562 | -1.8706 | 0.1702 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 1033 | 31 | -0.2069 | -1.1961 | 0.2903 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 30 | 30 | 2.0238 | 2.9609 | 0.6 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1400_close` | 18 | 18 | 1.4469 | 2.3012 | 0.6667 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 146, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1409 | 930 | -0.4232 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `latency_state` | `simulated` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1401 | 930 | -0.4232 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1279 | 925 | -0.4165 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1240 | 897 | -0.4274 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1202 | 853 | -0.4207 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1077 | 763 | -0.4568 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1054 | 751 | -0.4292 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 994 | 708 | -0.4182 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 894 | 644 | -0.4439 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 686 | 496 | -0.5328 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 636 | 496 | -0.5328 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 636 | 496 | -0.5328 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 649 | 431 | -0.2978 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 649 | 431 | -0.2978 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 597 | 396 | -0.2871 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 397 | 316 | -0.6887 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 429 | 276 | -0.1749 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 238 | 185 | -0.4664 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 208 | 162 | -0.2267 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 201 | 155 | -0.4841 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 256 | 141 | -0.4244 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 171 | 108 | -0.3576 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 257 | 77 | -0.4513 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 69 | 51 | -0.2731 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 62 | 49 | -0.5003 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 39 | 37 | -0.3066 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 114 | 36 | -0.3109 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 58 | 34 | -0.6004 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 219 | 33 | -0.3088 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 48 | 33 | -0.3088 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 48 | 33 | -0.3088 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 48 | 32 | -0.2481 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1287 | 930 | -0.9562 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1287 | 930 | -0.9562 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 740 | 707 | -1.4687 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 975 | 689 | -0.9845 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 530 | 530 | -1.4821 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 268 | 203 | -0.8389 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 146 | 146 | -1.3925 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 70 | 64 | 0.8468 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 66 | 57 | 0.2164 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 46 | 46 | 0.8217 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 46 | 42 | 2.3997 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 42 | 42 | 0.2027 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 44 | 38 | -1.0677 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 54 | 31 | -0.0452 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 31 | 31 | -1.5973 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 30 | 30 | 2.6064 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 57 | 29 | -0.5783 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 21 | 21 | -0.6748 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 20 | 20 | -0.1567 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 17 | 17 | 0.9232 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 13 | 13 | 0.202 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | 0.116 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.7912 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 8 | 8 | -0.325 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 2.1578 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.598 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.5733 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 0.7014 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 103 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 79 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 357 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 103 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 286 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 65 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_020_180s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 67, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1268 | 1268 | -1.3278 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 853 | 853 | -1.0382 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 795 | 795 | -0.8601 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 795 | 795 | -0.8601 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 795 | 795 | -0.8601 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 546 | 546 | -1.1692 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 385 | 385 | -1.2147 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 345 | 345 | -1.5413 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 305 | 305 | -1.7961 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 282 | 282 | -0.4424 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 231 | 231 | -0.5119 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 226 | 226 | -1.0138 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 201 | 201 | -0.5158 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 149 | 149 | 0.9183 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 149 | 149 | -1.6751 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 136 | 136 | -1.0817 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 127 | 127 | -1.1692 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 118 | 118 | -2.5732 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 8712 | 103 | 0.0767 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 103 | 103 | 0.0767 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 103 | 103 | 0.0767 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 99 | 99 | -0.7166 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 74 | 74 | 0.9783 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 69 | 69 | 0.2971 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 60 | 60 | -1.5946 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 57 | 57 | 0.0719 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 52 | 52 | 2.7595 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 33 | 33 | -0.9059 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 29 | 29 | 0.2948 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 27 | 27 | -0.2708 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 25 | 25 | 0.2388 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 25 | 25 | 1.5833 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 24 | 24 | 0.145 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 23 | 23 | -0.4451 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 21 | 21 | 1.0829 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 14 | 14 | 0.7254 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 14 | 14 | 3.1308 | `candidate_recovery_or_relax` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 11 | 11 | -0.8301 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 11 | 11 | 1.0036 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 10 | 10 | 0.2925 | `hold_no_edge` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 730, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 59036 | 59036 | None | -0.459 | 0.207 | `hold_sample` |
| `arm` | `AVG_DOWN` | 46631 | 46371 | None | -0.7721 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 39107 | 39107 | None | -0.4479 | 0.2141 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 31994 | 31734 | None | -0.9395 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 14637 | 14637 | None | -0.4093 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 13556 | 12690 | None | 0.6877 | 0.9647 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 13556 | 12690 | None | 0.6877 | 0.9647 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 10393 | 10393 | None | -0.4847 | 0.1891 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 10102 | 10102 | None | 0.485 | 0.9773 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 6991 | 6991 | None | -0.3473 | 0.1232 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 4957 | 4957 | None | -0.5001 | 0.1963 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2690 | 2690 | None | -0.4895 | 0.1848 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1889 | 1889 | None | -0.3984 | 0.2202 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1336 | 1336 | None | -0.4439 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 947 | 947 | None | -0.8278 | 0.1088 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 859 | 859 | None | 3.0023 | 1.0 | `hold_sample` |
| `blocker_reason` | `ok` | 575 | 575 | None | -2.5299 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 458 | 458 | None | -1.09 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_scale_in_window_expansion` | 446 | 446 | None | -0.3272 | 0.3498 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 425 | 425 | None | -0.75 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 206 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 103 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 206 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 103 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 206 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 103 | 103 | 0.0767 | 0.1022 | 0.3689 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 198 | 99 | 0.0867 | 0.1157 | 0.3838 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 158 | 79 | 0.2235 | 0.298 | 0.4304 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 130 | 65 | -0.5767 | -0.7689 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 33 | 33 | -0.9059 | -1.2079 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 66 | 33 | -0.9059 | -1.2079 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 28 | 28 | -0.2638 | -0.3518 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 56 | 28 | -0.2638 | -0.3518 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 23 | 23 | 0.1546 | 0.2061 | 0.8261 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 46 | 23 | 0.1546 | 0.2061 | 0.8261 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 38 | 19 | 0.1978 | 0.2637 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 36 | 18 | -0.3808 | -0.5078 | 0.2222 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 9 | 9 | 0.8258 | 1.1011 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 18 | 9 | 0.8258 | 1.1011 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 18 | 9 | 0.8258 | 1.1011 | 1.0 | `hold_sample` |

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
