# Lifecycle Decision Matrix - 2026-06-26

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-26_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `244891`
- source_rows_total: `357753`
- retained_rows: `244891`
- dropped_rows_by_source: `{}`
- joined_rows: `214772`
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
- lifecycle_flow_bucket_count: `984`
- lifecycle_flow_complete_count: `1270`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0057`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 14509 | 1965 | 0.7001 | 0.9448 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 4812 | 3172 | -0.5213 | 0.9982 | `pass` | `NO_CHANGE` | False |
| `holding` | 4544 | 3172 | -0.9511 | 0.998 | `pass` | `EXIT` | False |
| `scale_in` | 203217 | 200705 | -0.4287 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 17809 | 5758 | -0.9447 | 0.9913 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 984, 'complete_flow_count': 1270, 'incomplete_flow_count': 220887, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 156629 | 155891 | -0.7307 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 44083 | 42309 | 0.7055 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 2069 | 2069 | -1.0412 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 446 | 446 | 1.448 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 367 | 367 | 1.7027 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 225 | 225 | 1.7235 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 183 | 183 | -0.2222 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 68 | 68 | -0.9251 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 43 | 43 | -0.7733 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 38 | 38 | -0.8637 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 30 | 30 | -1.0348 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 24 | 24 | -1.9926 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 18 | 18 | -0.9387 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 17 | 17 | -0.5952 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 16 | 16 | -0.8968 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 16 | 16 | -1.3182 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 15 | 15 | -0.8072 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 14 | 14 | -1.2605 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 13 | 13 | -1.0217 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 559, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 10043 | 1956 | 0.7004 | 0.7586 | 0.454 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 9552 | 1476 | 0.5942 | 0.2777 | 0.4336 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 1045 | 1045 | 1.594 | 2.5414 | 0.6469 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 13589 | 1045 | 1.594 | 2.5414 | 0.6469 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 10453 | 841 | -0.3112 | -1.2991 | 0.2307 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 798 | 798 | 1.3498 | 2.174 | 0.6253 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 6703 | 749 | -0.3198 | -1.3391 | 0.2203 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 2890 | 721 | 1.3171 | 2.1217 | 0.6311 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 6648 | 700 | 0.0185 | -0.7552 | 0.2871 | `source_quality_workorder` |
| `strength_bucket` | `strong_strength_momentum` | 1543 | 669 | 1.0912 | 1.6639 | 0.5785 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 5774 | 624 | -0.2918 | -1.284 | 0.2308 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 3142 | 541 | 0.718 | 0.7991 | 0.488 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 1370 | 485 | 0.9114 | 1.3972 | 0.5546 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 6622 | 457 | -0.3494 | -1.4213 | 0.2035 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 447 | 447 | -0.2319 | -1.9792 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 2652 | 403 | 0.4392 | 0.1703 | 0.3921 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 627 | 313 | 1.3642 | 2.0464 | 0.5974 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 1505 | 262 | 0.8215 | 1.3032 | 0.4962 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 1067 | 233 | 0.8532 | 1.2358 | 0.4979 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 232 | 232 | -0.2612 | -3.0257 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1844 | 217 | 0.0179 | -0.1364 | 0.3502 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 205 | 205 | -0.5477 | 2.0547 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 116 | 116 | 1.2408 | 1.7372 | 0.6379 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 192, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 4654 | 3172 | -0.5213 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 4266 | 3172 | -0.5213 | `keep_collecting` |
| `latency_state` | `simulated` | 4266 | 3172 | -0.5213 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 4637 | 3172 | -0.5213 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 4217 | 3137 | -0.5076 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 3975 | 2971 | -0.5382 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 3642 | 2702 | -0.5284 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 3486 | 2573 | -0.561 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 2594 | 1936 | -0.553 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 2346 | 1777 | -0.6643 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 2193 | 1777 | -0.6643 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 2193 | 1777 | -0.6643 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 2277 | 1664 | -0.432 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 2019 | 1533 | -0.6649 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1934 | 1426 | -0.4042 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2038 | 1392 | -0.3391 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 2038 | 1392 | -0.3391 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1765 | 1363 | -0.6143 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1723 | 1173 | -0.3154 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 1288 | 930 | -0.4232 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 1240 | 914 | -0.5379 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 760 | 564 | -0.2644 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 795 | 470 | -0.4805 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 397 | 316 | -0.6887 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 429 | 276 | -0.1749 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 764 | 204 | -0.2726 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 291 | 201 | -0.2717 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 291 | 201 | -0.2717 | `keep_collecting` |
| `would_limit_fill` | `false` | 836 | 200 | -0.2733 | `keep_collecting` |
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
| `held_bucket` | `held_not_applicable_at_start` | 4265 | 3172 | -0.9511 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 4265 | 3172 | -0.9511 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2482 | 2377 | -1.4475 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 2085 | 1556 | -1.0284 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1970 | 1443 | -0.8547 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1168 | 1168 | -1.5038 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1062 | 1062 | -1.3853 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 263 | 241 | 0.2067 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 216 | 204 | 0.6275 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 210 | 173 | -1.0597 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 215 | 155 | 0.0277 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 147 | 147 | -1.4487 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 137 | 129 | 2.1101 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 122 | 122 | 0.1057 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 115 | 115 | 0.2963 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 100 | 100 | 0.7327 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 95 | 95 | 0.0243 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 93 | 93 | 0.4957 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 67 | 67 | 2.2777 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 138 | 66 | -0.4617 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 58 | 58 | 0.0026 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 53 | 53 | 1.9487 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 41 | 41 | -0.5404 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 25 | 25 | -0.3324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.8122 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.7123 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.919 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 279 | 0 | None | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 73 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 200 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1093 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 279 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 37 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 527 | 0 | None | `hold_sample` |
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
| `profit_band` | `profit_lt_neg070` | 4283 | 4283 | -1.3329 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3004 | 3004 | -1.0116 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2475 | 2475 | -0.9589 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2475 | 2475 | -0.9589 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2475 | 2475 | -0.9589 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1838 | 1838 | -1.1935 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 1341 | 1341 | -1.2801 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 1167 | 1167 | -1.5133 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 1058 | 1058 | -0.5178 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 917 | 917 | -1.8058 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 779 | 779 | -0.9306 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 638 | 638 | 0.5938 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 626 | 626 | -0.5128 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 547 | 547 | -0.5329 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 493 | 493 | -1.7155 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 445 | 445 | -1.1703 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 402 | 402 | -0.8708 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 398 | 398 | -1.2559 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 366 | 366 | -2.4594 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 12330 | 279 | -0.0987 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 279 | 279 | -0.0987 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 279 | 279 | -0.0987 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 258 | 258 | 0.2455 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 226 | 226 | 0.064 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 221 | 221 | 0.7494 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 153 | 153 | -1.6731 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 144 | 144 | 2.4076 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 105 | 105 | -0.9504 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 93 | 93 | -0.4084 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 90 | 90 | 0.1085 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 79 | 79 | 1.2155 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 71 | 71 | -0.2886 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 63 | 63 | 0.3271 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 61 | 61 | 0.2265 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 59 | 59 | 0.783 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 56 | 56 | 2.5073 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 52 | 52 | 1.0091 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 49 | 49 | 0.2598 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 43 | 43 | -0.5098 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 1099, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 200658 | 200658 | None | -0.4955 | 0.2066 | `hold_sample` |
| `arm` | `AVG_DOWN` | 158921 | 158183 | None | -0.8018 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 113979 | 113979 | None | -0.4929 | 0.2067 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 111266 | 110528 | None | -0.9655 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 47655 | 47655 | None | -0.4221 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 44296 | 42522 | None | 0.6453 | 0.9758 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 44296 | 42522 | None | 0.6453 | 0.9758 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 37570 | 37570 | None | -0.4707 | 0.2146 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 35699 | 35699 | None | 0.5167 | 0.9811 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 26007 | 26007 | None | -0.5163 | 0.2058 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 19344 | 19344 | None | -0.3304 | 0.1575 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 12833 | 12833 | None | -0.5086 | 0.1923 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10269 | 10269 | None | -0.5459 | 0.1963 | `hold_sample` |
| `blocker_reason` | `low_broken` | 4531 | 4531 | None | -0.4567 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 2870 | 2870 | None | -0.8397 | 0.0885 | `hold_sample` |
| `blocker_reason` | `ok` | 1833 | 1833 | None | -2.408 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1664 | 1664 | None | 3.223 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1565 | 1565 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1526 | 1526 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1410 | 1410 | None | -1.1 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 558 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 279 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 558 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 279 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 558 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 279 | 279 | -0.0987 | -0.1316 | 0.3369 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 550 | 275 | -0.0976 | -0.1302 | 0.3418 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 400 | 200 | -0.0216 | -0.0288 | 0.37 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 370 | 185 | -0.6525 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 105 | 105 | -0.9504 | -1.2671 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 210 | 105 | -0.9504 | -1.2671 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 146 | 73 | -0.2783 | -0.3711 | 0.274 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 72 | 72 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 144 | 72 | -0.2856 | -0.3808 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 60 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 120 | 60 | 0.2315 | 0.3087 | 0.8667 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 104 | 52 | 0.274 | 0.3654 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 22 | 22 | 0.8482 | 1.1309 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 44 | 22 | 0.8482 | 1.1309 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 44 | 22 | 0.8482 | 1.1309 | 1.0 | `hold_sample` |

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
