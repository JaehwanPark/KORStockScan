# Lifecycle Decision Matrix - 2026-05-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-29_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `137254`
- source_rows_total: `137254`
- retained_rows: `137254`
- dropped_rows_by_source: `{}`
- joined_rows: `132432`
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
- lifecycle_flow_bucket_count: `232`
- lifecycle_flow_complete_count: `165`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0068`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3350 | 408 | 0.6277 | 0.9077 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1170 | 783 | -0.7652 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1111 | 783 | -0.7769 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 127270 | 127152 | -0.3033 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 4353 | 3306 | -0.5722 | 0.9995 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 232, 'complete_flow_count': 165, 'incomplete_flow_count': 24150, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 52229 | 52182 | -0.6152 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 15156 | 15144 | 0.6097 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 260 | 260 | -0.4312 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 257 | 257 | -0.6021 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 99 | 99 | 0.4783 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 83 | 83 | -0.4989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 80 | 80 | -0.4405 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 63 | 63 | 0.3689 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 53 | 53 | -0.1351 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 46 | 46 | -0.1122 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 111 | 32 | -1.5546 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 633 | 22 | -1.0451 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b3f591e69a` | 19 | 19 | -0.7663 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5814d62155` | 16 | 16 | -0.4431 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:b75dcb4fef` | 16 | 16 | -0.3538 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 15 | 15 | -0.0523 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:f87fa0c80c` | 13 | 13 | -0.6131 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:34cc4a9d10` | 12 | 12 | -0.0461 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 291, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `exit_unknown` | 3249 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 1318 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 307 | 307 | 1.1842 | 1.9857 | 0.5342 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 2811 | 231 | 0.8065 | 1.7399 | 0.5238 | `candidate_tighten_or_exclude` |
| `score_band` | `score_70p` | 768 | 221 | 0.863 | 1.7914 | 0.5249 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 2131 | 215 | 0.9814 | 1.9422 | 0.5302 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 177 | 177 | 0.3944 | 0.7571 | 0.4689 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_high` | 177 | 177 | 0.3944 | 0.7571 | 0.4689 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 316 | 152 | 0.4135 | 0.8156 | 0.454 | `hold_sample` |
| `chosen_action` | `action_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `strength_bucket` | `strength_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_unknown` | 779 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 942 | 123 | -0.1841 | 0.2061 | 0.4553 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 194 | 113 | 0.864 | 1.3909 | 0.5221 | `hold_sample` |
| `strength_bucket` | `risk_unknown` | 1564 | 101 | -1.0637 | -0.7295 | 0.3961 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1563 | 101 | -1.0637 | -0.7295 | 0.3961 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 1580 | 95 | -1.0278 | -0.6193 | 0.4211 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 88 | 88 | 0.4042 | 0.6885 | 0.4886 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_0900_1000` | 813 | 81 | -0.5221 | -0.4586 | 0.4321 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 1954 | 58 | -0.9161 | -0.8319 | 0.3621 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 614 | 58 | -0.3008 | -0.3141 | 0.3793 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_watch` | 50 | 50 | 0.6136 | 0.9606 | 0.52 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `chosen_action` | `BUY_NOW` | 65 | 43 | -1.2627 | -0.5914 | 0.4418 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 1780 | 43 | -0.8873 | -0.9414 | 0.3488 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 40 | 40 | -1.1479 | 1.4328 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 39 | 39 | -0.7231 | -1.9292 | 0.0 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 30 | 30 | -0.3388 | -0.0814 | 0.3333 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 20 | 20 | 1.0562 | 1.4859 | 0.55 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 18 | 18 | -1.0431 | -1.62 | 0.5 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 190 | 16 | -1.5448 | -0.9781 | 0.4375 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 16 | 16 | -1.9 | -2.6502 | 0.25 | `candidate_tighten_or_exclude` |

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
| `liquidity_guard_action` | `would_pass` | 1210 | 921 | -0.7863 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1314 | 802 | -0.7657 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1168 | 785 | -0.7648 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `latency_state` | `simulated` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1028 | 762 | -0.765 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1044 | 720 | -0.6502 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 936 | 707 | -0.7416 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 900 | 645 | -0.735 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 926 | 641 | -0.729 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 896 | 641 | -0.729 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 691 | 527 | -0.7188 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 735 | 497 | -0.5881 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 672 | 457 | -0.5639 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 549 | 394 | -0.5697 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 351 | 301 | -1.0579 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 281 | 252 | -1.1033 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 312 | 229 | -0.8575 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 216 | 153 | -0.5899 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 159 | 142 | -0.9283 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 130 | 119 | -0.9299 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 88 | 80 | -0.6005 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 119 | 76 | -0.9837 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 76 | 59 | -2.1046 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 71 | 53 | -1.0431 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 39 | 34 | -0.8463 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 28 | 28 | -2.3678 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 23 | 22 | -1.5233 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 27 | 21 | -0.7701 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 161 | 21 | -0.7701 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 27 | 21 | -0.7701 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 23 | 17 | -0.7431 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 17 | 15 | -1.9033 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 5 | -1.558 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -4.0362 | `source_quality_workorder` |
| `overbought_bucket` | `pullback_or_rebreak_not_confirmed` | 4 | 4 | -1.6867 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -1.4313 | `source_quality_workorder` |
| `price_resolution_bucket` | `ai_tier2_use_defensive` | 4 | 3 | -1.035 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_overbought_guard_would_block` | 2 | 2 | -2.4932 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=false|submitted=false` | 2 | 2 | -1.1562 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 66, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_source_stage` | `scalp_sim_holding_started` | 1055 | 783 | -0.7769 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 678 | 466 | -0.7 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 474 | 464 | -1.5646 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 663 | 392 | -0.9653 | `source_quality_workorder` |
| `held_bucket` | `held_not_applicable_at_start` | 392 | 391 | -0.588 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_unknown` | 245 | 175 | -1.0868 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 145 | 145 | -1.5619 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 132 | 132 | -1.5007 | `source_quality_workorder` |
| `holding_action` | `holding_action_not_applicable_at_start` | 125 | 124 | -0.6099 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 106 | 106 | -1.6377 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 95 | 90 | 0.2283 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 96 | 86 | -0.2384 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 93 | 82 | 0.5609 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 66 | 66 | -1.6457 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 50 | 46 | 1.703 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 40 | 40 | 0.7206 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 27 | 27 | 0.5043 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 26 | 26 | 0.0166 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 26 | 26 | 0.2199 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 26 | 26 | -0.4381 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 24 | 24 | -0.2238 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 19 | 19 | 1.8757 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 19 | 19 | 0.2533 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 32 | 18 | -0.9056 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 17 | 17 | -0.2719 | `source_quality_workorder` |
| `profit_band` | `profit_neg070_neg010` | 31 | 15 | -0.448 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 15 | 15 | 0.7207 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 15 | 15 | 0.6178 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 1.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 12 | 12 | -0.2423 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.4172 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 9 | 9 | -1.6396 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 9 | 9 | -0.3488 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 7 | 7 | 1.7258 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -0.7367 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 5 | 5 | 1.0928 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.9726 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 2 | 2 | 0.9238 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 2 | 2 | -0.2168 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.0295 | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 91, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2472 | 2472 | -0.5443 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2472 | 2472 | -0.5443 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 2644 | 1597 | -0.4805 | `source_quality_workorder` |
| `profit_band` | `profit_lt_neg070` | 1430 | 1430 | -1.2982 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 1139 | 1139 | -0.4676 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 987 | 987 | -0.5334 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 722 | 722 | -0.8282 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 702 | 702 | -0.4768 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 553 | 553 | -1.1699 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 414 | 414 | -1.2007 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 401 | 401 | -0.4678 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 367 | 367 | 0.146 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 297 | 297 | -1.3644 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 251 | 251 | 0.3262 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 235 | 235 | -0.1549 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 224 | 224 | -1.2853 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 212 | 212 | -1.9105 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 190 | 190 | -0.8228 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 184 | 184 | 0.474 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 164 | 164 | 0.2547 | `source_quality_workorder` |
| `profit_band` | `profit_pos080_pos150` | 151 | 151 | 0.609 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 151 | 151 | 1.2555 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 110 | 110 | 0.283 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 101 | 101 | -2.5405 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 91 | 91 | -1.1451 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 74 | 74 | -1.7748 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 72 | 72 | -1.1979 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300_plus` | 68 | 68 | 2.3827 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 58 | 58 | -0.9016 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 38 | 38 | -1.6385 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 36 | 36 | -0.0994 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 32 | 32 | -0.44 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 31 | 31 | 1.1448 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 30 | 30 | 0.8195 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 28 | 28 | 2.0529 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 26 | 26 | 1.1346 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 26 | 26 | 2.2962 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 25 | 25 | -0.6713 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 22 | 22 | -0.1247 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 338, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 115908 | 115814 | -0.7322 | -0.7987 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 92486 | 92486 | -0.2803 | -0.3174 | 0.2632 | `hold_no_edge` |
| `ai_score_source` | `ai_source_unknown` | 83684 | 83613 | -0.3652 | -0.4108 | 0.2299 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 46398 | 46256 | 0.783 | 0.7462 | 0.9848 | `candidate_recovery_or_relax` |
| `ai_score_source` | `score_field_backfilled` | 43538 | 43538 | -0.1844 | -0.2176 | 0.3055 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 36716 | 36716 | -0.2979 | -0.2951 | 0.2655 | `hold_no_edge` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20143 | 20143 | -0.0311 | -0.013 | 0.3573 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 18802 | 18802 | -0.3554 | -0.4243 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 13927 | 13927 | -0.279 | -0.3117 | 0.2493 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 12850 | 12850 | 0.5811 | 0.5257 | 0.989 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 11481 | 11481 | -0.3089 | -0.3346 | 0.1941 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 11293 | 11293 | -0.2133 | -0.2345 | 0.2223 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 5103 | 5103 | -0.9713 | -1.1586 | 0.2214 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 4342 | 4342 | -0.3221 | -0.3596 | 0.2464 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 2754 | 2754 | -0.3521 | -0.3751 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 822 | 822 | -0.3893 | -0.4062 | 0.0973 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 528 | 528 | 2.7136 | 2.719 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 481 | 481 | -0.6606 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 466 | 466 | -0.7283 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 429 | 429 | -0.7305 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 423 | 423 | -0.0178 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 410 | 410 | -0.0441 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `ok` | 398 | 398 | -5.512 | -6.8698 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 398 | 398 | -0.7196 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 397 | 397 | -0.7592 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 393 | 393 | -0.0427 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 352 | 352 | -0.8717 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 345 | 345 | -0.8925 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.03)` | 309 | 309 | -0.9197 | -1.03 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 307 | 307 | -0.6823 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 307 | 307 | -1.0491 | -1.16 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 304 | 304 | -0.7048 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 303 | 303 | -0.8155 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 303 | 303 | -0.9963 | -1.1 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 291 | 291 | -0.8399 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 290 | 290 | -0.8254 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 287 | 287 | -0.9765 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 283 | 283 | -0.6614 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 224 | 168 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `stage` | `exit` | 112 | 112 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 168 | 112 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 159 | 106 | 0.496 | 0.6613 | 0.4906 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 112 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `confidence_band` | `confidence_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `held_bucket` | `held_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 56 | 56 | 0.4602 | 0.6136 | 0.4643 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 102 | 51 | 0.5037 | 0.6716 | 0.4706 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 48 | 32 | -0.2339 | -0.3119 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 60 | 30 | -0.3875 | -0.5167 | 0.0 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 33 | 22 | 1.6739 | 2.2318 | 1.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 30 | 20 | -0.765 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 30 | 20 | 0.111 | 0.148 | 0.6 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 16 | 16 | -0.2339 | -0.3119 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 16 | 16 | -0.2339 | -0.3119 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300` | 11 | 11 | 1.6739 | 2.2318 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 10 | 10 | -0.765 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 10 | 0.111 | 0.148 | 0.6 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 10 | 10 | -0.765 | -1.02 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 10 | 10 | 0.111 | 0.148 | 0.6 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 12 | 8 | 3.4725 | 4.63 | 1.0 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_zero_pos080` | 12 | 6 | 0.2238 | 0.2983 | 1.0 | `hold_no_edge` |

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
