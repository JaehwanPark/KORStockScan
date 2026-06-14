# Lifecycle Decision Matrix - 2026-06-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-11_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `103746`
- source_rows_total: `172984`
- retained_rows: `103746`
- dropped_rows_by_source: `{}`
- joined_rows: `97403`
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
- lifecycle_flow_bucket_count: `473`
- lifecycle_flow_complete_count: `485`
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
| `entry` | 4380 | 831 | 0.4862 | 0.9953 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 1957 | 1657 | -0.5266 | 0.9966 | `pass` | `NO_CHANGE` | False |
| `holding` | 1844 | 1657 | -0.8988 | 0.9961 | `pass` | `EXIT` | False |
| `scale_in` | 90457 | 90106 | -0.4106 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 5108 | 3152 | -0.9522 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 473, 'complete_flow_count': 485, 'incomplete_flow_count': 94787, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 67464 | 67334 | -0.7407 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 21628 | 21407 | 0.6552 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1147 | 1147 | -1.093 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 183 | 183 | 1.3108 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 133 | 133 | 1.3106 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 124 | 124 | 1.0774 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 98 | 98 | -0.3721 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 34 | 34 | -0.9123 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 22 | 22 | -0.9105 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 20 | 20 | -0.8595 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 9 | 9 | -1.1989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:53bb9c05e0` | 9 | 9 | -0.7924 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 8 | 8 | -1.0437 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 7 | 7 | -1.7184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 7 | 7 | -0.6166 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 7 | 7 | -0.3182 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7092a0ecba` | 7 | 7 | -1.0192 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 357, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2391 | 829 | 0.4893 | 0.6229 | 0.4704 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 2041 | 557 | 0.448 | 0.1422 | 0.4524 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 440 | 440 | 1.245 | 2.1599 | 0.6364 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3989 | 440 | 1.245 | 2.1599 | 0.6364 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 2408 | 368 | -0.3578 | -1.177 | 0.2663 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1501 | 326 | 0.7711 | 1.4404 | 0.6074 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 326 | 326 | 0.7711 | 1.4404 | 0.6074 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 1162 | 315 | -0.1381 | -0.8193 | 0.3206 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 997 | 304 | -0.3586 | -1.1877 | 0.273 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 1215 | 303 | -0.3585 | -1.1951 | 0.2706 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 1000 | 284 | 0.293 | 0.2917 | 0.4894 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 402 | 281 | 0.7036 | 1.2792 | 0.5837 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 1575 | 193 | -0.3871 | -1.1009 | 0.2694 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 183 | 183 | -0.2852 | -1.9736 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 822 | 169 | 0.3494 | 0.1825 | 0.426 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 293 | 137 | 0.4345 | 1.0022 | 0.562 | `source_quality_workorder` |
| `score_band` | `score_63_65` | 295 | 130 | 0.6161 | 0.9294 | 0.5077 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 316 | 127 | 0.2611 | 2.0022 | 0.5433 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 499 | 125 | 0.7432 | 0.7984 | 0.456 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 693 | 123 | 0.1981 | 0.305 | 0.4228 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 108 | 108 | -0.6434 | 1.7059 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 59 | 59 | 0.7906 | 1.1097 | 0.6271 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 90, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1878 | 1657 | -0.5266 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1722 | 1657 | -0.5266 | `keep_collecting` |
| `latency_state` | `simulated` | 1722 | 1657 | -0.5266 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1870 | 1657 | -0.5266 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1697 | 1633 | -0.5148 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1598 | 1539 | -0.5447 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1415 | 1358 | -0.5248 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1409 | 1336 | -0.5687 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1123 | 1079 | -0.6306 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1095 | 1005 | -0.6112 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1035 | 1005 | -0.6112 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1035 | 1005 | -0.6112 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1013 | 971 | -0.5761 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 996 | 953 | -0.542 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 686 | 652 | -0.3961 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 686 | 652 | -0.3961 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 610 | 592 | -0.4147 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 597 | 582 | -0.5512 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 581 | 562 | -0.6282 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 550 | 522 | -0.3716 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 469 | 454 | -0.3486 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 381 | 359 | -0.3728 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 307 | 299 | -0.5347 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 307 | 297 | -0.2722 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 221 | 213 | -0.5281 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 155 | 150 | -0.4032 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 142 | 141 | -0.3094 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 359 | 118 | -0.2912 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 124 | 118 | -0.2912 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 360 | 118 | -0.2912 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 124 | 118 | -0.2912 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 110 | 104 | -0.1069 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 98 | 93 | -0.7286 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 35 | 35 | -2.1838 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 25 | 25 | -0.569 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 25 | 24 | -1.3338 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 25 | 24 | -1.3338 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 17 | 16 | -0.7283 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 14 | 14 | -1.6608 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 12 | 12 | -2.492 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1722 | 1657 | -0.8988 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1722 | 1657 | -0.8988 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1242 | 1196 | -1.4218 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1125 | 1079 | -0.9975 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 792 | 792 | -1.4891 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 493 | 482 | -0.6751 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 325 | 325 | -1.2872 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 162 | 151 | 0.1595 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 119 | 113 | 0.5428 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 136 | 110 | 0.0131 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 97 | 97 | 0.0289 | `hold_sample` |
| `holding_action` | `BUY` | 104 | 96 | -0.9132 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 79 | 79 | -1.3014 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 78 | 78 | -0.0174 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 70 | 66 | 1.9916 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 63 | 63 | 0.4074 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 52 | 52 | 0.3775 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 40 | 40 | 0.6936 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 37 | 37 | 2.1629 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 32 | 32 | 0.0874 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 24 | 24 | 1.911 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 50 | 21 | -0.339 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 12 | 12 | -0.3342 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.3452 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 1.111 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 122 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 39 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 83 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 65 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 122 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 46 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 32 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 14 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 9 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 70, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2339 | 2339 | -1.3292 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1679 | 1679 | -0.9504 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1351 | 1351 | -1.0283 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1041 | 1041 | -1.2253 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 725 | 725 | -1.282 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 647 | 647 | -1.4473 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 616 | 616 | -0.4793 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 471 | 471 | -1.7574 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 420 | 420 | 0.4502 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 416 | 416 | -0.8754 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 312 | 312 | -0.5146 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 279 | 279 | -0.5406 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 265 | 265 | -1.6894 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 236 | 236 | -0.8787 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 224 | 224 | -1.2251 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 208 | 208 | -1.2271 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 190 | 190 | -2.3605 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 159 | 159 | 0.1684 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 152 | 152 | 0.033 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 2078 | 122 | -0.1345 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 122 | 122 | -0.1345 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 122 | 122 | -0.1345 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 119 | 119 | 0.6584 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 73 | 73 | -1.6987 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 71 | 71 | 2.2234 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 60 | 60 | -0.4709 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 59 | 59 | -0.4457 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 47 | 47 | 1.0072 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 46 | 46 | -1.0797 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 45 | 45 | 0.0035 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 43 | 43 | 0.2934 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 41 | 41 | -0.5096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 41 | 41 | 0.7657 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 36 | 36 | 0.4157 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 32 | 32 | 2.284 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 29 | 29 | -0.3109 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 28 | 28 | -0.034 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 26 | 26 | 0.2651 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 521, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 90101 | 90101 | None | -0.489 | 0.2337 | `hold_sample` |
| `arm` | `AVG_DOWN` | 68724 | 68594 | None | -0.8254 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 48929 | 48799 | None | -0.9888 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 46422 | 46422 | None | -0.4975 | 0.2315 | `hold_sample` |
| `arm` | `PYRAMID` | 21733 | 21512 | None | 0.5839 | 0.979 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 21733 | 21512 | None | 0.5839 | 0.979 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 19795 | 19795 | None | -0.4226 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 18984 | 18984 | None | 0.5382 | 0.9811 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 17861 | 17861 | None | -0.442 | 0.2548 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 14300 | 14300 | None | -0.5013 | 0.2341 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 7450 | 7450 | None | -0.2989 | 0.2036 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 6445 | 6445 | None | -0.4978 | 0.2098 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 5073 | 5073 | None | -0.5306 | 0.2091 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1920 | 1920 | None | -0.4507 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1552 | 1552 | None | -0.876 | 0.0825 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1008 | 1008 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 928 | 928 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 923 | 923 | None | -2.3614 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 851 | 851 | None | -0.78 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 794 | 794 | None | -1.37 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 244 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 122 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 244 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 122 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 244 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 244 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 122 | 122 | -0.1345 | -0.1793 | 0.3607 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 166 | 83 | -0.1066 | -0.1422 | 0.3735 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 156 | 78 | -0.7541 | -1.0055 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 46 | 46 | -1.0797 | -1.4396 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 92 | 46 | -1.0797 | -1.4396 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 78 | 39 | -0.1938 | -0.2585 | 0.3333 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 29 | 29 | -0.3109 | -0.4145 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 58 | 29 | -0.3109 | -0.4145 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 26 | 26 | 0.2651 | 0.3535 | 0.8846 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 52 | 26 | 0.2651 | 0.3535 | 0.8846 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 46 | 23 | 0.3058 | 0.4078 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 11 | 11 | 0.8461 | 1.1282 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 22 | 11 | 0.8461 | 1.1282 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 22 | 11 | 0.8461 | 1.1282 | 1.0 | `hold_sample` |

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
