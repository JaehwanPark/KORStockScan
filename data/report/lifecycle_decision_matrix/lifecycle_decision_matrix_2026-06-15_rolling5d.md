# Lifecycle Decision Matrix - 2026-06-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-15_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `55181`
- source_rows_total: `76959`
- retained_rows: `55181`
- dropped_rows_by_source: `{}`
- joined_rows: `48549`
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
- lifecycle_flow_bucket_count: `328`
- lifecycle_flow_complete_count: `281`
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
| `entry` | 3034 | 360 | -0.0248 | 0.909 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1598 | 782 | -0.7736 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1508 | 782 | -0.9419 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 45931 | 45360 | -0.4705 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 3110 | 1265 | -0.9432 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 328, 'complete_flow_count': 281, 'incomplete_flow_count': 48879, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 36529 | 36306 | -0.7363 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 8824 | 8476 | 0.6865 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 488 | 488 | -0.9984 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 58 | 58 | 0.6193 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 46 | 46 | 1.8264 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 38 | 38 | 0.2388 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 18 | 18 | -0.875 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 16 | 16 | 0.7912 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 13 | 13 | -0.8879 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 11 | 11 | -0.9591 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 11 | 11 | -1.1064 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 8 | 8 | -0.8738 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f7df4238eb` | 6 | 6 | 0.9657 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 5 | 5 | -0.7854 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:be2863195a` | 4 | 4 | -0.8648 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 4 | 4 | -0.2417 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a6f1cf48c2` | 4 | 4 | -3.1019 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a2a88f9390` | 4 | 4 | -2.5656 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:d3405d70cf` | 4 | 4 | -0.975 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 4 | 4 | -0.2494 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 280, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 2149 | 360 | -0.0248 | -0.1507 | 0.3917 | `hold_no_edge` |
| `overbought_bucket` | `overbought_normal` | 1958 | 252 | 0.2652 | -0.1856 | 0.3929 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 2095 | 240 | -0.5897 | -1.1485 | 0.2625 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1846 | 240 | -0.5897 | -1.1485 | 0.2625 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2254 | 234 | -0.5755 | -1.1673 | 0.2607 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `weak_strength_momentum` | 1895 | 210 | -0.4226 | -1.0297 | 0.281 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 1628 | 154 | -0.6494 | -1.1708 | 0.2532 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 1112 | 151 | 0.3412 | 0.1538 | 0.4239 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 365 | 130 | 0.7248 | 1.2308 | 0.5615 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 120 | 120 | 1.1049 | 1.8448 | 0.65 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2794 | 120 | 1.1049 | 1.8448 | 0.65 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 721 | 120 | 1.1049 | 1.8448 | 0.65 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 120 | 120 | 1.1049 | 1.8448 | 0.65 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 104 | 104 | -0.4167 | -2.0186 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 751 | 99 | 0.5844 | 0.6726 | 0.5051 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 931 | 84 | -0.9245 | -1.1217 | 0.2738 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 135 | 65 | 0.4917 | 0.6956 | 0.5077 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 63 | 63 | -0.5216 | -2.9135 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 61 | 61 | -1.1806 | 1.9918 | 1.0 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 184 | 60 | 1.1271 | 2.0364 | 0.6666 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 205 | 56 | -1.6375 | -0.3896 | 0.3393 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_watch` | 226 | 45 | 0.4528 | 0.5478 | 0.4889 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 822 | 42 | -0.2675 | -1.0288 | 0.2857 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 265 | 39 | 0.0699 | 0.0478 | 0.4359 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 261 | 38 | -0.5035 | -1.0645 | 0.2631 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 382 | 32 | -0.1082 | -1.6403 | 0.125 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 29 | 29 | 1.143 | 1.6956 | 0.6552 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 140 | 28 | 0.4942 | -0.3132 | 0.3929 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1400_close` | 240 | 26 | -1.5631 | -1.9173 | 0.1538 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `neutral_strength_momentum` | 173 | 20 | -0.72 | 0.0979 | 0.45 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 84, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1555 | 782 | -0.7736 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1435 | 782 | -0.7736 | `keep_collecting` |
| `latency_state` | `simulated` | 1435 | 782 | -0.7736 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1555 | 782 | -0.7736 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 1411 | 768 | -0.7494 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1296 | 714 | -0.8104 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1172 | 657 | -0.8336 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 1156 | 643 | -0.8522 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 853 | 502 | -0.8997 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 884 | 474 | -1.0498 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 759 | 422 | -0.9621 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 685 | 395 | -0.9417 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 643 | 395 | -0.9417 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 643 | 395 | -0.9417 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 760 | 387 | -0.602 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 760 | 387 | -0.602 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 608 | 310 | -0.5848 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 559 | 309 | -0.4553 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 410 | 261 | -1.0886 | `source_quality_workorder` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 404 | 238 | -0.3289 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 416 | 225 | -0.6376 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 398 | 209 | -0.6287 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 263 | 125 | -0.458 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 265 | 125 | -0.2207 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 177 | 80 | -0.5042 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 139 | 68 | -0.3875 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 334 | 68 | -0.3875 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 139 | 68 | -0.3875 | `keep_collecting` |
| `would_limit_fill` | `false` | 301 | 67 | -0.3941 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 124 | 58 | -0.0734 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 103 | 58 | -0.8152 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 116 | 51 | -1.142 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 68 | 44 | -0.4118 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 24 | 14 | -2.1002 | `keep_collecting` |
| `overbought_guard_action` | `would_block` | 24 | 14 | -2.1002 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 20 | 12 | -0.7766 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 13 | 9 | -2.8149 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 14 | 9 | -2.4611 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 16 | 9 | -1.2218 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_overbought_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=pullback_or_rebreak_not_confirmed|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 10 | 7 | -2.7841 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 46, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 1435 | 782 | -0.9419 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1435 | 782 | -0.9419 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 580 | 547 | -1.5192 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 932 | 490 | -1.1518 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 354 | 354 | -1.6272 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 447 | 257 | -0.4857 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 164 | 164 | -1.2366 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 76 | 72 | 0.1034 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 65 | 63 | 0.4116 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 45 | 45 | -0.0498 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 56 | 42 | -0.1695 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 40 | 39 | 1.9666 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 56 | 35 | -1.3515 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 32 | 32 | -0.2523 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 31 | 31 | 0.0579 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 29 | 29 | -1.7994 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 29 | 29 | 0.7587 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 26 | 26 | 0.3811 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 22 | 22 | 2.2774 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 38 | 19 | -0.4458 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 16 | 16 | 1.5558 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 12 | 12 | -0.395 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.0346 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 7 | 7 | -0.533 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 0.7116 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -0.2245 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 1.7039 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 73 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 23 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 50 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 653 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 73 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 21 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 190 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 442 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 11 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 22 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 11 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 65, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 920 | 920 | -1.3557 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 612 | 612 | -1.0558 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 580 | 580 | -0.9157 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 580 | 580 | -0.9157 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 580 | 580 | -0.9157 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 432 | 432 | -1.1538 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 262 | 262 | -1.4744 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 232 | 232 | -1.4424 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 220 | 220 | -0.6918 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 169 | 169 | -1.8833 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 160 | 160 | -0.9959 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 153 | 153 | 0.444 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 148 | 148 | -0.5188 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 128 | 128 | -0.5442 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 97 | 97 | -1.9228 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 92 | 92 | -1.3094 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 86 | 86 | -1.522 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 1918 | 73 | -0.2177 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 73 | 73 | -0.2177 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 73 | 73 | -0.2177 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 73 | 73 | -1.0863 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 60 | 60 | -2.4074 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 58 | 58 | 0.6048 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 51 | 51 | 0.1152 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 50 | 50 | -0.0785 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 38 | 38 | 2.4668 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 33 | 33 | -0.8741 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 29 | 29 | 0.1031 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 25 | 25 | -0.6566 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 23 | 23 | -1.8672 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 19 | 19 | -0.3202 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 18 | 18 | 1.0153 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 17 | 17 | 0.0913 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 15 | 15 | -0.3957 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 15 | 15 | -0.5975 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 15 | 15 | 1.9654 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 14 | 14 | 0.2662 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 13 | 13 | -0.7204 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 13 | 13 | 1.3785 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 13 | 13 | 0.5617 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 311, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 45353 | 45353 | None | -0.5338 | 0.1833 | `hold_sample` |
| `arm` | `AVG_DOWN` | 37065 | 36842 | None | -0.8058 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 25398 | 25175 | None | -0.9826 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 21687 | 21687 | None | -0.5367 | 0.1781 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 11667 | 11667 | None | -0.4243 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 8710 | 8710 | None | -0.4916 | 0.2 | `hold_sample` |
| `arm` | `PYRAMID` | 8866 | 8518 | None | 0.644 | 0.9766 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 8866 | 8518 | None | 0.644 | 0.9766 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 8268 | 8268 | None | -0.5138 | 0.186 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 7528 | 7528 | None | 0.4985 | 0.977 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3598 | 3598 | None | -0.5424 | 0.1746 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 3090 | 3090 | None | -0.6756 | 0.1754 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 2417 | 2417 | None | -0.377 | 0.115 | `hold_sample` |
| `blocker_reason` | `low_broken` | 1196 | 1196 | None | -0.4703 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 652 | 652 | None | -0.7373 | 0.089 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 465 | 465 | None | -0.73 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 433 | 433 | None | -0.86 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 420 | 420 | None | -0.98 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 407 | 407 | None | -1.16 | 0.0 | `hold_sample` |
| `blocker_reason` | `ok` | 395 | 395 | None | -2.3715 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 146 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 73 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 146 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `stage` | `exit` | 73 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 146 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 146 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 73 | 73 | -0.2177 | -0.2903 | 0.2603 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 108 | 54 | -0.6478 | -0.8637 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 100 | 50 | -0.182 | -0.2426 | 0.26 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 33 | 33 | -0.8741 | -1.1655 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 66 | 33 | -0.8741 | -1.1655 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 46 | 23 | -0.2954 | -0.3939 | 0.2609 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 19 | 19 | -0.3202 | -0.4269 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 38 | 19 | -0.3202 | -0.4269 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 14 | 14 | 0.2662 | 0.355 | 0.8571 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 28 | 14 | 0.2662 | 0.355 | 0.8571 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 24 | 12 | 0.315 | 0.42 | 1.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 4 | 4 | 0.9956 | 1.3275 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 8 | 4 | 0.9956 | 1.3275 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 8 | 4 | 0.9956 | 1.3275 | 1.0 | `hold_sample` |

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
