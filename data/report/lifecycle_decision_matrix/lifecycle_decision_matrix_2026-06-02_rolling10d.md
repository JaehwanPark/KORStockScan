# Lifecycle Decision Matrix - 2026-06-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-02_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `183437`
- source_rows_total: `220067`
- retained_rows: `183437`
- dropped_rows_by_source: `{}`
- joined_rows: `176430`
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
- lifecycle_flow_bucket_count: `399`
- lifecycle_flow_complete_count: `386`
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
| `entry` | 5058 | 804 | 1.1435 | 0.9532 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1974 | 1496 | -0.6396 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1874 | 1496 | -0.8132 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 168155 | 168018 | -0.3296 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6376 | 4616 | -0.6772 | 0.9997 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 399, 'complete_flow_count': 386, 'incomplete_flow_count': 66810, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 83618 | 83563 | -0.6335 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 24019 | 24006 | 0.6065 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 809 | 809 | -0.9297 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 261 | 261 | 1.4365 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 260 | 260 | -0.4312 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 180 | 180 | 1.862 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 83 | 83 | -0.4989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 80 | 80 | -0.4405 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 72 | 72 | -0.214 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 53 | 53 | -0.1351 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 40 | 40 | 1.0659 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 112 | 32 | -1.5546 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 652 | 22 | -1.0451 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 19 | 19 | -0.7663 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 16 | 16 | -0.4431 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 16 | 16 | -0.3538 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 13 | 13 | -0.6131 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 13 | 13 | -0.6523 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 326, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `exit_unknown` | 4865 | 611 | 1.7127 | 2.7943 | 0.581 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 2317 | 611 | 1.7127 | 2.7943 | 0.581 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 611 | 611 | 1.7127 | 2.7943 | 0.581 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 481 | 481 | 1.5649 | 2.5608 | 0.5696 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 481 | 481 | 1.5649 | 2.5608 | 0.5696 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 1231 | 404 | 1.2587 | 2.32 | 0.5619 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 622 | 399 | 1.5157 | 2.5024 | 0.5664 | `hold_sample` |
| `liquidity_bucket` | `liquidity_unknown` | 3520 | 323 | 0.5161 | 1.0495 | 0.4799 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 2543 | 295 | 0.7007 | 1.2812 | 0.4983 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 245 | 245 | 1.6251 | 2.5551 | 0.5755 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 367 | 235 | 1.7537 | 2.774 | 0.5702 | `hold_sample` |
| `strength_bucket` | `risk_unknown` | 2026 | 193 | -0.6582 | -0.7079 | 0.3834 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 2025 | 193 | -0.6582 | -0.7079 | 0.3834 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 2125 | 185 | -0.6277 | -0.6339 | 0.4 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1000_1200` | 1177 | 185 | 0.6307 | 1.2843 | 0.5189 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_watch` | 133 | 133 | 1.6198 | 2.6678 | 0.5789 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 2632 | 131 | -0.4863 | -0.8508 | 0.3435 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `strength_bucket` | `strength_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 821 | 115 | 0.8814 | 1.5101 | 0.5565 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 2579 | 87 | -0.5704 | -1.0222 | 0.3218 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 78 | 78 | -0.4712 | -1.9027 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 74 | 74 | -0.5226 | 1.5943 | 1.0 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 68 | 68 | 1.1207 | 2.0362 | 0.5294 | `candidate_tighten_or_exclude` |
| `chosen_action` | `BUY_NOW` | 88 | 62 | -1.0213 | -0.406 | 0.4677 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 41 | 41 | 1.1545 | 1.8579 | 0.5854 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 38 | 38 | 0.7779 | 1.1354 | 0.579 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 33 | 33 | -0.7527 | -1.1118 | 0.3939 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 236 | 27 | -1.4996 | -1.3426 | 0.2963 | `candidate_tighten_or_exclude` |

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
| `liquidity_guard_action` | `would_pass` | 2090 | 1784 | -0.6477 | `keep_collecting` |
| `actual_order_submitted` | `false` | 2206 | 1530 | -0.6467 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1979 | 1501 | -0.6413 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1782 | 1496 | -0.6396 | `keep_collecting` |
| `latency_state` | `simulated` | 1782 | 1496 | -0.6396 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1737 | 1457 | -0.6304 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1790 | 1394 | -0.5291 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1559 | 1317 | -0.6186 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1474 | 1208 | -0.6277 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1521 | 1203 | -0.6233 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1469 | 1203 | -0.6233 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1177 | 930 | -0.5148 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1048 | 825 | -0.4667 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 917 | 747 | -0.6399 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 786 | 696 | -0.6181 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 683 | 627 | -0.8419 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 745 | 584 | -0.5063 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 542 | 509 | -0.8543 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 494 | 427 | -0.4995 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 313 | 293 | -0.7065 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 265 | 251 | -0.6453 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 228 | 179 | -0.7945 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 144 | 126 | -0.6087 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 111 | 106 | -0.4921 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 111 | 103 | -0.5574 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 119 | 97 | -2.1739 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 63 | 57 | -0.7584 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 50 | 39 | -0.9844 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 257 | 39 | -0.9844 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 50 | 39 | -0.9844 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 31 | 31 | -2.4145 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 36 | 30 | -0.9913 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 27 | 26 | -1.6756 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 14 | 14 | -0.6872 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 14 | 14 | -3.8028 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 7 | 7 | -0.9087 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_lt1s` | 7 | 7 | -0.5518 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -3.3253 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -0.0627 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 5 | 5 | -1.6833 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 74, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_source_stage` | `scalp_sim_holding_started` | 1787 | 1496 | -0.8132 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 1119 | 1104 | -0.7592 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 984 | 965 | -1.4868 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1125 | 904 | -0.7481 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 448 | 448 | -1.424 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 668 | 392 | -0.9653 | `source_quality_workorder` |
| `holding_action` | `holding_action_not_applicable_at_start` | 392 | 386 | -0.8369 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 253 | 253 | -1.5425 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 250 | 175 | -1.0868 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 160 | 154 | 0.1634 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 165 | 147 | -0.1107 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 132 | 132 | -1.5007 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300` | 143 | 130 | 0.6595 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 106 | 106 | -1.6377 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 80 | 75 | 1.7914 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 71 | 71 | 0.7941 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 66 | 66 | 0.0914 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 65 | 65 | 0.1986 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 44 | 44 | 0.172 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 38 | 38 | 1.7735 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 32 | 32 | 0.6704 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 45 | 31 | -0.8751 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 31 | 31 | -0.1787 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 26 | 26 | 0.2199 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 26 | 26 | -0.4381 | `source_quality_workorder` |
| `profit_band` | `profit_neg070_neg010` | 51 | 25 | -0.4326 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 24 | 24 | -0.2238 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 22 | 22 | 2.0578 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 17 | 17 | -1.1831 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 17 | 17 | -0.2719 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 15 | 15 | 0.7207 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 12 | 12 | -0.2423 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 10 | 10 | -0.5693 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 9 | 9 | -1.6396 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 9 | 9 | -0.3488 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 7 | 7 | 1.7258 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 5 | 5 | 1.0928 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3875 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.799 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 2 | 2 | 0.9238 | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 98, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 3074 | 3074 | -0.642 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 3074 | 3074 | -0.642 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2383 | 2383 | -1.3079 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 3388 | 1628 | -0.4719 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1589 | 1589 | -0.7266 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1399 | 1399 | -0.8601 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 1288 | 1288 | -0.4752 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 869 | 869 | -1.2143 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 702 | 702 | -0.4768 | `source_quality_workorder` |
| `exit_outcome` | `GOOD_EXIT` | 574 | 574 | -1.3852 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 553 | 553 | -1.1699 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 539 | 539 | -0.4892 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 479 | 479 | -0.2626 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 471 | 471 | -1.2549 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 436 | 436 | -1.8125 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 433 | 433 | 0.1371 | `hold_no_edge` |
| `exit_rule` | `scalp_trailing_take_profit` | 433 | 433 | 0.3817 | `hold_no_edge` |
| `exit_outcome` | `NEUTRAL` | 346 | 346 | -0.8161 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 246 | 246 | 0.3471 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 217 | 217 | 0.4558 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 202 | 202 | -2.4344 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 198 | 198 | 1.1497 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 165 | 165 | -1.1608 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 164 | 164 | 0.2547 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 163 | 163 | -1.1438 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 162 | 162 | -1.7041 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 143 | 143 | -0.863 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 116 | 116 | 0.2854 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 97 | 97 | 2.2353 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 70 | 70 | -1.6023 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 61 | 61 | -0.4873 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 54 | 54 | -0.0714 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 54 | 54 | 0.8051 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 45 | 45 | -0.5928 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 37 | 37 | 1.0519 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 37 | 37 | 0.2215 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 37 | 37 | -0.0287 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 36 | 36 | 1.3799 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 31 | 31 | 1.1448 | `source_quality_workorder` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 418, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 169684 | 169574 | -0.7355 | -0.8065 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 113774 | 113774 | -0.299 | -0.343 | 0.2573 | `hold_no_edge` |
| `ai_score_source` | `score_field_backfilled` | 84389 | 84389 | -0.2845 | -0.3351 | 0.261 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `ai_source_unknown` | 83714 | 83628 | -0.3751 | -0.4232 | 0.2298 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 64204 | 64040 | 0.7217 | 0.6771 | 0.9836 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 28990 | 28990 | -0.3582 | -0.4231 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 21428 | 21428 | -0.3127 | -0.3545 | 0.2273 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20852 | 20852 | -0.0608 | -0.0433 | 0.3467 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 20046 | 20046 | 0.5758 | 0.521 | 0.9883 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 18075 | 18075 | -0.3031 | -0.3265 | 0.1892 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 16657 | 16657 | -0.3033 | -0.3385 | 0.2075 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 8976 | 8976 | -0.8005 | -0.9625 | 0.2232 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 7182 | 7182 | -0.3377 | -0.3848 | 0.2285 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 4019 | 4019 | -0.3758 | -0.4009 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 1112 | 1112 | -0.3258 | -0.3431 | 0.1385 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 845 | 845 | 2.6524 | 2.661 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 756 | 756 | -4.2967 | -5.3697 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 704 | 704 | -0.7316 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 624 | 624 | -0.8522 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 609 | 609 | -0.6625 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 583 | 583 | -0.7382 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 573 | 573 | -0.69 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 568 | 568 | -0.7173 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 565 | 565 | -0.7597 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 542 | 542 | -0.0376 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 542 | 542 | -0.6654 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 529 | 529 | -0.0122 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 509 | 509 | -0.0399 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 501 | 501 | -0.9749 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 500 | 500 | -0.865 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 495 | 495 | -0.7129 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 478 | 478 | -0.8926 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 472 | 472 | -0.767 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 469 | 469 | -0.8246 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 462 | 462 | -0.8242 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 453 | 453 | -0.9499 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 449 | 449 | -1.0626 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 317 | 230 | 0.3282 | 0.4376 | 0.4348 | `hold_sample` |
| `stage` | `exit` | 143 | 143 | 0.354 | 0.472 | 0.4405 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 230 | 143 | 0.354 | 0.472 | 0.4405 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 221 | 137 | 0.3771 | 0.5028 | 0.4598 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 174 | 87 | 0.2857 | 0.3809 | 0.4253 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 87 | 87 | 0.2857 | 0.3809 | 0.4253 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 128 | 64 | 0.383 | 0.5106 | 0.4531 | `hold_sample` |
| `overnight_action` | `action_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `confidence_band` | `confidence_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `held_bucket` | `held_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 98 | 49 | -0.4429 | -0.5906 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 68 | 42 | -0.2509 | -0.3345 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 48 | 29 | -0.7699 | -1.0266 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 46 | 28 | 0.1216 | 0.1621 | 0.6786 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 26 | 26 | -0.2613 | -0.3485 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 37 | 24 | 1.6784 | 2.2379 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 44 | 22 | 0.0235 | 0.0314 | 0.3636 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 19 | 19 | -0.7725 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 18 | 18 | 0.1275 | 0.17 | 0.7222 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 28 | 14 | 0.1805 | 0.2407 | 0.9286 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 10 | 10 | -0.765 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.111 | 0.148 | 0.6 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 14 | 9 | 3.5117 | 4.6822 | 1.0 | `candidate_recovery_or_relax` |

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
