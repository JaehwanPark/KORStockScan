# Lifecycle Decision Matrix - 2026-06-10

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-10_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `71600`
- source_rows_total: `120928`
- retained_rows: `71600`
- dropped_rows_by_source: `{}`
- joined_rows: `67632`
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
- lifecycle_flow_bucket_count: `316`
- lifecycle_flow_complete_count: `317`
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
| `entry` | 2776 | 557 | 0.5979 | 1.0 | `pass` | `NO_CHANGE` | False |
| `submit` | 1274 | 1108 | -0.4013 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1174 | 1108 | -0.939 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 63291 | 62943 | -0.4059 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3085 | 1916 | -0.9837 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 316, 'complete_flow_count': 317, 'incomplete_flow_count': 65896, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 46461 | 46334 | -0.7687 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 15996 | 15775 | 0.6849 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 722 | 722 | -1.1244 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 146 | 146 | 1.2367 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 88 | 88 | 1.5796 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 79 | 79 | 0.7596 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 60 | 60 | -0.5658 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 13 | 13 | -0.8408 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 11 | 11 | -0.9118 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:aee8bb0d09` | 7 | 7 | -1.0471 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ec33ba7790` | 6 | 6 | -1.9202 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 6 | 6 | -1.771 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 6 | 6 | -1.06 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f3928c3e95` | 5 | 5 | -0.9619 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9c99306a62` | 4 | 4 | -1.4857 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:bbc4a80a0b` | 4 | 4 | -1.6452 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:5035e8a5e2` | 4 | 4 | -1.0644 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:af7d5c8fc1` | 3 | 3 | -1.7142 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:fddb29efa4` | 3 | 3 | -1.0195 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:8b8602048c` | 3 | 3 | -0.7941 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 289, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 1596 | 557 | 0.5979 | 0.6382 | 0.4542 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 1366 | 376 | 0.4797 | 0.1169 | 0.4255 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 313 | 313 | 1.2127 | 2.0974 | 0.6198 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2532 | 313 | 1.2127 | 2.0974 | 0.6198 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1485 | 225 | -0.1627 | -1.306 | 0.2178 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 834 | 199 | 0.4178 | 0.883 | 0.5628 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 199 | 199 | 0.4178 | 0.883 | 0.5628 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 436 | 172 | -0.1035 | -1.1559 | 0.2558 | `hold_no_edge` |
| `strength_bucket` | `strong_strength_momentum` | 212 | 167 | 0.5472 | 0.9626 | 0.5569 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 342 | 157 | -0.0754 | -1.4278 | 0.2038 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 454 | 157 | 0.1212 | -0.0203 | 0.465 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 413 | 156 | -0.0732 | -1.4437 | 0.1987 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 122 | 122 | -0.1874 | -1.9581 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 423 | 112 | 0.3945 | 0.1519 | 0.375 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 750 | 105 | -0.0628 | -1.3465 | 0.2 | `hold_no_edge` |
| `overbought_bucket` | `overbought_watch` | 282 | 90 | 0.736 | 0.7022 | 0.4222 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 163 | 90 | 0.1117 | 0.5136 | 0.5111 | `hold_no_edge` |
| `overbought_bucket` | `overbought_ok` | 195 | 75 | 0.8498 | 2.4485 | 0.6267 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 144 | 72 | 0.2162 | 0.1345 | 0.4167 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 314 | 63 | 0.1887 | -0.5896 | 0.3333 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 89 | 62 | 0.7963 | 1.0077 | 0.6129 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 57 | 57 | -0.1732 | 1.706 | 1.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 53 | 53 | -0.2337 | -2.8721 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1400_close` | 156 | 24 | -0.1578 | -1.0471 | 0.3333 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1517 | 1494 | -0.3336 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1501 | 1182 | -0.3765 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1123 | 1108 | -0.4013 | `keep_collecting` |
| `latency_state` | `simulated` | 1123 | 1108 | -0.4013 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1272 | 1108 | -0.4013 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1049 | 1034 | -0.4296 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 902 | 887 | -0.3911 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 908 | 880 | -0.4455 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 804 | 800 | -0.4839 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 729 | 722 | -0.5411 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 722 | 718 | -0.4249 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 760 | 708 | -0.5265 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 715 | 708 | -0.5265 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 606 | 592 | -0.3452 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 440 | 439 | -0.5458 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 408 | 400 | -0.1795 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 375 | 368 | -0.4823 | `source_quality_workorder` |
| `price_below_bid_bucket` | `not_below_bid` | 337 | 326 | -0.3003 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 329 | 321 | -0.1841 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 240 | 229 | -0.2484 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 221 | 221 | -0.4419 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 214 | 214 | -0.1619 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 214 | 207 | -0.0878 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 162 | 162 | -0.4977 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 114 | 114 | -0.2256 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 104 | 103 | -0.4011 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 74 | 74 | -0.0054 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 225 | 74 | -0.0054 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 74 | 74 | -0.0054 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 67 | 67 | 0.0659 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 63 | 63 | -0.6608 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 30 | 30 | -2.3126 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 15 | 15 | -0.7789 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 14 | 14 | -1.2802 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 10 | -0.2277 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | 0.0779 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 7 | 7 | -0.6878 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 5 | 5 | -0.031 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 5 | 5 | -2.459 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.678 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1123 | 1108 | -0.939 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1123 | 1108 | -0.939 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 867 | 852 | -1.3972 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 790 | 787 | -0.9937 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 606 | 606 | -1.4641 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 237 | 233 | -0.7292 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 169 | 169 | -1.1977 | `candidate_tighten_or_exclude` |
| `holding_action` | `BUY` | 96 | 88 | -1.0053 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 96 | 88 | 0.2916 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 77 | 77 | -1.3082 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 78 | 64 | 0.1544 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 61 | 61 | 0.1909 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 64 | 60 | 0.6204 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 48 | 48 | 0.1657 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 44 | 44 | 0.5994 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 38 | 36 | 2.2009 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 26 | 26 | 0.4672 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 24 | 24 | 2.5037 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 16 | 16 | 0.1207 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 9 | 9 | 1.6162 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 9 | 9 | 0.5615 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2535 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 7 | 7 | 0.8275 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2943 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.2127 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 3 | 3 | 1.5324 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.8776 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 51 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 22 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 29 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 15 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 51 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 6 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 67, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1478 | 1478 | -1.3235 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1038 | 1038 | -0.9601 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 827 | 827 | -1.0719 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 827 | 827 | -1.0719 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 827 | 827 | -1.0719 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 655 | 655 | -1.2417 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 436 | 436 | -1.1995 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 402 | 402 | -1.5309 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 374 | 374 | -0.4516 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 320 | 320 | -1.7949 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 262 | 262 | -0.81 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 223 | 223 | 0.5634 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 170 | 170 | -0.5238 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 165 | 165 | -1.5741 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 158 | 158 | -0.5439 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 141 | 141 | -0.8078 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 140 | 140 | -2.378 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 130 | 130 | -1.2057 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 130 | 130 | -1.1489 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 102 | 102 | -0.0338 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 90 | 90 | 0.2898 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 81 | 81 | 0.1664 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 60 | 60 | 0.6614 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 56 | 56 | -0.435 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1220 | 51 | -0.0338 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 50 | 50 | -1.6941 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 37 | 37 | 2.1951 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 31 | 31 | -0.3752 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 25 | 25 | 0.8542 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 23 | 23 | -0.4776 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 23 | 23 | 1.0515 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 22 | 22 | 0.5153 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 22 | 22 | 0.3835 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 19 | 19 | -0.1988 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 19 | 19 | 0.1089 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 18 | 18 | 2.461 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 17 | 17 | -0.8004 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 16 | 16 | -0.3676 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 15 | 15 | -1.4575 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 14 | 14 | 0.2802 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 303, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 81883 | 81629 | -0.8374 | -0.9242 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 62938 | 62938 | -0.406 | -0.4885 | 0.247 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 34426 | 34426 | -0.4177 | -0.505 | 0.2394 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 32116 | 31674 | 0.6838 | 0.6078 | 0.9818 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 13922 | 13922 | 0.6411 | 0.5586 | 0.9843 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 12583 | 12583 | -0.3501 | -0.4219 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 10896 | 10896 | -0.3089 | -0.3932 | 0.2874 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 9950 | 9950 | -0.4593 | -0.5227 | 0.2414 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 4995 | 4995 | -0.2582 | -0.2805 | 0.2283 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 3838 | 3838 | -0.4119 | -0.4968 | 0.2259 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 3828 | 3828 | -0.4331 | -0.5155 | 0.2364 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 1295 | 1295 | -0.4327 | -0.4586 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 949 | 949 | -0.9376 | -0.9374 | 0.0759 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 841 | 841 | -1.0536 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 790 | 790 | -0.8544 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 719 | 719 | -1.256 | -1.37 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 693 | 693 | -0.7216 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 673 | 673 | -0.9245 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 663 | 663 | -1.9397 | -2.3827 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 652 | 652 | -1.0112 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 629 | 629 | -0.652 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.43)` | 616 | 616 | -1.2658 | -1.43 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.18)` | 490 | 490 | -1.0926 | -1.18 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 470 | 470 | -0.8635 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.05)` | 410 | 410 | -0.9717 | -1.05 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.04)` | 402 | 402 | -0.9392 | -1.04 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 395 | 395 | -0.9347 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 384 | 384 | -0.8071 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 382 | 382 | -0.6507 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 373 | 373 | -0.7825 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 338 | 338 | -0.1387 | -0.1944 | 0.3846 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 325 | 325 | -0.7556 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.93)` | 311 | 311 | -0.8497 | -0.93 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 307 | 307 | -1.0279 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 306 | 306 | -0.0399 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 304 | 304 | -0.6625 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 292 | 292 | -0.7338 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 290 | 290 | -0.8747 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.30)` | 286 | 286 | -1.1825 | -1.3 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.34)` | 286 | 286 | -1.2243 | -1.34 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 153 | 102 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 102 | 51 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 51 | 51 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 102 | 51 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 102 | 51 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 51 | 51 | -0.0338 | -0.0451 | 0.5098 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 58 | 29 | -0.0266 | -0.0355 | 0.5862 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 50 | 25 | -0.9738 | -1.2984 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 44 | 22 | -0.0433 | -0.0577 | 0.4091 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 15 | 15 | -1.4575 | -1.9434 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 30 | 15 | -1.4575 | -1.9434 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 14 | 14 | 0.2802 | 0.3736 | 0.8571 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 28 | 14 | 0.2802 | 0.3736 | 0.8571 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 24 | 12 | 0.3356 | 0.4475 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.2972 | -0.3962 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 8 | 8 | 0.7753 | 1.0337 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 16 | 8 | 0.7753 | 1.0337 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.2972 | -0.3962 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 16 | 8 | 0.7753 | 1.0337 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 4 | 4 | 1.5094 | 2.0125 | 1.0 | `hold_sample` |

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
