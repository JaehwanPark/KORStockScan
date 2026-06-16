# Lifecycle Decision Matrix - 2026-06-16

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-16_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `164688`
- source_rows_total: `252279`
- retained_rows: `164688`
- dropped_rows_by_source: `{}`
- joined_rows: `151364`
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
- lifecycle_flow_bucket_count: `663`
- lifecycle_flow_complete_count: `760`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.005`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 7702 | 1229 | 0.5716 | 0.9701 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3353 | 2242 | -0.562 | 0.9975 | `pass` | `NO_CHANGE` | False |
| `holding` | 3154 | 2242 | -0.9489 | 0.9971 | `pass` | `EXIT` | False |
| `scale_in` | 143030 | 141644 | -0.4396 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7449 | 4007 | -0.9678 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 663, 'complete_flow_count': 760, 'incomplete_flow_count': 149782, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 110715 | 110237 | -0.7378 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 30613 | 29705 | 0.6888 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1421 | 1421 | -1.0727 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 247 | 247 | 1.4106 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 204 | 204 | 1.4727 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 169 | 169 | 1.5396 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 116 | 116 | -0.2587 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 48 | 48 | -0.9294 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 29 | 29 | -0.919 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 28 | 28 | -0.8625 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 16 | 16 | -1.1775 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 15 | 15 | -1.4425 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 12 | 12 | -1.9752 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:c7f35b773f` | 12 | 12 | -1.9011 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 11 | 11 | -0.6112 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 10 | 10 | -0.2715 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:727c304d19` | 10 | 10 | -2.0274 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 9 | 9 | -0.9933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 9 | 9 | -0.8339 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:05b084aa57` | 9 | 9 | -0.8524 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 414, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 4999 | 1227 | 0.5738 | 0.6387 | 0.4556 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 4600 | 877 | 0.4708 | 0.1327 | 0.4356 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 620 | 620 | 1.4662 | 2.4042 | 0.6516 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 7093 | 620 | 1.4662 | 2.4042 | 0.6516 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 5159 | 573 | -0.3166 | -1.2138 | 0.2461 | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2495 | 438 | -0.3561 | -1.2563 | 0.2397 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 2889 | 437 | -0.356 | -1.2616 | 0.238 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 2672 | 432 | -0.1549 | -0.917 | 0.287 | `source_quality_workorder` |
| `stale_bucket` | `fresh_or_unflagged` | 1770 | 373 | 0.8591 | 1.5273 | 0.6086 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 373 | 373 | 0.8591 | 1.5273 | 0.6086 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 1778 | 347 | 0.3026 | 0.1763 | 0.4553 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 650 | 336 | 0.7299 | 1.2528 | 0.5655 | `source_quality_workorder` |
| `exit_rule` | `scalp_soft_stop_pct` | 293 | 293 | -0.2361 | -1.9818 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_60_62` | 2659 | 281 | -0.3857 | -1.2401 | 0.2313 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 1333 | 222 | 0.4422 | 0.3525 | 0.4324 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 543 | 219 | 0.679 | 1.3127 | 0.589 | `source_quality_workorder` |
| `time_bucket` | `time_1200_1400` | 1375 | 176 | -0.0208 | -0.2569 | 0.3409 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 728 | 161 | 1.053 | 1.2635 | 0.4845 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 495 | 158 | 0.5065 | 2.2722 | 0.5253 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 151 | 151 | -0.5952 | 1.9017 | 1.0 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 86 | 86 | 0.9676 | 1.3104 | 0.6512 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 99, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3245 | 2242 | -0.562 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2978 | 2242 | -0.562 | `keep_collecting` |
| `latency_state` | `simulated` | 2978 | 2242 | -0.562 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3236 | 2242 | -0.562 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2938 | 2212 | -0.5457 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2735 | 2074 | -0.5861 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2440 | 1849 | -0.5781 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2409 | 1810 | -0.6048 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1781 | 1348 | -0.6921 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1700 | 1292 | -0.6074 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1660 | 1281 | -0.7152 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1557 | 1281 | -0.7152 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1557 | 1281 | -0.7152 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1564 | 1208 | -0.6311 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1389 | 961 | -0.3577 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1389 | 961 | -0.3577 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1223 | 913 | -0.4343 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1126 | 777 | -0.3298 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 984 | 773 | -0.5587 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 900 | 730 | -0.7803 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 940 | 718 | -0.3904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 749 | 523 | -0.3211 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 552 | 402 | -0.2796 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 538 | 393 | -0.4862 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 312 | 264 | -0.5974 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 343 | 232 | -0.3937 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 206 | 179 | -0.3483 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 243 | 168 | -0.2644 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 650 | 168 | -0.2644 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 243 | 168 | -0.2644 | `keep_collecting` |
| `would_limit_fill` | `false` | 617 | 167 | -0.2663 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 221 | 151 | -0.1159 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 188 | 119 | -0.8492 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 46 | 39 | -2.0609 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 43 | 34 | -0.732 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 40 | 30 | -1.7602 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 40 | 30 | -1.7602 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 22 | 17 | -0.8126 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 20 | 16 | -2.6943 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 21 | 16 | -1.6853 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2978 | 2242 | -0.9489 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2978 | 2242 | -0.9489 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1742 | 1670 | -1.4385 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1817 | 1353 | -1.0568 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1022 | 1022 | -1.5197 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 995 | 754 | -0.736 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 532 | 532 | -1.2889 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 197 | 184 | 0.2038 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 146 | 140 | 0.5272 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 166 | 135 | -1.0575 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 161 | 124 | 0.0459 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 116 | 116 | -1.409 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 109 | 109 | 0.0943 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 91 | 87 | 1.9702 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 85 | 85 | 0.0135 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 76 | 76 | 0.4001 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 73 | 73 | 0.3502 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 54 | 54 | 0.6569 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 44 | 44 | 1.9809 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 38 | 38 | 0.0864 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 81 | 37 | -0.3703 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 37 | 37 | 2.0112 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 20 | 20 | -0.3994 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 17 | 17 | -0.3359 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 10 | 10 | 0.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 1.6394 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 176 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 55 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 121 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 736 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 176 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 241 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 464 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 50 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 13 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 24 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3015 | 3015 | -1.335 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2151 | 2151 | -1.001 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1680 | 1680 | -1.0057 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1680 | 1680 | -1.0057 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1680 | 1680 | -1.0057 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1292 | 1292 | -1.2038 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 956 | 956 | -1.3064 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 822 | 822 | -1.5015 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 776 | 776 | -0.5452 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 612 | 612 | -1.8107 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 553 | 553 | -0.8966 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 489 | 489 | 0.4949 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 395 | 395 | -0.5133 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 346 | 346 | -0.5429 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 344 | 344 | -1.7329 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 309 | 309 | -1.2093 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 303 | 303 | -0.9211 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 271 | 271 | -1.2965 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 248 | 248 | -2.4052 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 189 | 189 | 0.2266 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3618 | 176 | -0.2013 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.2013 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.2013 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 169 | 169 | 0.0613 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 147 | 147 | 0.6341 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 93 | 93 | -1.7238 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 92 | 92 | 2.2087 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 87 | 87 | -0.5005 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 72 | 72 | -0.9707 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 70 | 70 | -0.3963 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 61 | 61 | 0.0199 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 54 | 54 | 1.0453 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 53 | 53 | 0.3337 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 45 | 45 | 0.801 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 44 | 44 | -0.2995 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 42 | 42 | 2.2994 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 41 | 41 | -0.5096 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -0.4387 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 37 | 37 | 0.2793 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 36 | 36 | 0.4157 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 639, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 141622 | 141622 | None | -0.5107 | 0.2064 | `hold_sample` |
| `arm` | `AVG_DOWN` | 112290 | 111812 | None | -0.8141 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 79272 | 78794 | None | -0.9759 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 74872 | 74872 | None | -0.5164 | 0.2028 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 33018 | 33018 | None | -0.4278 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 30740 | 29832 | None | 0.6272 | 0.9805 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 30740 | 29832 | None | 0.6272 | 0.9805 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 27177 | 27177 | None | -0.4654 | 0.2244 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 25597 | 25597 | None | 0.5292 | 0.9827 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 21050 | 21050 | None | -0.5202 | 0.208 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 12353 | 12353 | None | -0.3209 | 0.1769 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 10143 | 10143 | None | -0.5136 | 0.1943 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 8380 | 8380 | None | -0.5792 | 0.1909 | `hold_sample` |
| `blocker_reason` | `low_broken` | 3195 | 3195 | None | -0.462 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1923 | 1923 | None | -0.8456 | 0.0785 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1371 | 1371 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 1258 | 1258 | None | -2.3523 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1255 | 1255 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1170 | 1170 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 1123 | 1123 | None | -0.82 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 352 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `overnight_status` | `SELL_TODAY` | 176 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `confidence_band` | `confidence_070p` | 352 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `stage` | `exit` | 176 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `price_source` | `holding_price_samples_last` | 352 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `source_quality_gate` | `overnight_decision_coverage` | 352 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 176 | 176 | -0.2013 | -0.2685 | 0.3182 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 242 | 121 | -0.1816 | -0.2421 | 0.3306 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 240 | 120 | -0.6936 | -0.9247 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 72 | 72 | -0.9707 | -1.2943 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 144 | 72 | -0.9707 | -1.2943 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 110 | 55 | -0.2448 | -0.3264 | 0.2909 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 44 | 44 | -0.2995 | -0.3993 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 88 | 44 | -0.2995 | -0.3993 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 37 | 37 | 0.2793 | 0.3724 | 0.8919 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 74 | 37 | 0.2793 | 0.3724 | 0.8919 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 66 | 33 | 0.3179 | 0.4239 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 13 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 26 | 13 | 0.8636 | 1.1515 | 1.0 | `hold_sample` |

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
