# Lifecycle Decision Matrix - 2026-05-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-29_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `230017`
- source_rows_total: `230017`
- retained_rows: `230017`
- dropped_rows_by_source: `{}`
- joined_rows: `219057`
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
- lifecycle_flow_bucket_count: `289`
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
| `entry` | 7568 | 839 | -0.0728 | 0.9186 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1743 | 1324 | -0.7251 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 1692 | 1324 | -0.6966 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 212287 | 210373 | -0.2529 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 6727 | 5197 | -0.5451 | 0.9997 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 289, 'complete_flow_count': 165, 'incomplete_flow_count': 24150, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 94868 | 94759 | -0.4315 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 23527 | 21863 | 0.5054 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 323 | 323 | -0.4399 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 1785 | 265 | -0.7216 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 260 | 260 | -0.4312 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 257 | 257 | -0.6021 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 99 | 99 | 0.4783 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 94 | 94 | -0.3934 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 83 | 83 | -0.4989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 63 | 63 | 0.3689 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9fa2e4711` | 1043 | 59 | -0.8086 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 53 | 53 | -0.1351 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 348 | 46 | -0.1868 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 46 | 46 | -0.1122 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:66ac2828ed` | 44 | 44 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 112 | 33 | -1.5549 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525` | 164 | 27 | -0.8248 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 242 | 26 | -1.481 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 327, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_unknown` | 7029 | 662 | -0.1978 | 0.3914 | 0.4335 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_unknown` | 5764 | 646 | -0.1644 | 0.4253 | 0.4334 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 4376 | 532 | -0.7982 | -0.4069 | 0.3872 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4367 | 526 | -0.7933 | -0.4098 | 0.3878 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 5330 | 481 | -0.7502 | -0.3973 | 0.3825 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 3404 | 417 | -0.7229 | -0.3977 | 0.3981 | `candidate_tighten_or_exclude` |
| `score_band` | `score_60_62` | 3897 | 314 | -0.7754 | -0.4525 | 0.3694 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_unknown` | 7036 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 2139 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 307 | 307 | 1.1842 | 1.9857 | 0.5342 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1652 | 258 | -0.3235 | -0.3845 | 0.438 | `hold_no_edge` |
| `time_bucket` | `time_1000_1200` | 2060 | 237 | -0.7013 | -0.1076 | 0.3966 | `hold_sample` |
| `score_band` | `score_70p` | 822 | 223 | 0.8456 | 1.7797 | 0.5247 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1732 | 189 | -0.7692 | -0.228 | 0.3598 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 184 | 177 | 0.3944 | 0.7571 | 0.4689 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 177 | 177 | 0.3944 | 0.7571 | 0.4689 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 169 | 169 | -1.0674 | 1.7556 | 1.0 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 567 | 152 | 0.4135 | 0.8156 | 0.454 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 137 | 137 | -0.858 | -1.8866 | 0.0073 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 1600 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 126 | 126 | -0.4229 | -0.3388 | 0.2064 | `candidate_tighten_or_exclude` |
| `score_band` | `score_lt60` | 2169 | 119 | -0.6285 | -0.2626 | 0.4285 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 398 | 108 | -0.3066 | -0.3808 | 0.4352 | `hold_no_edge` |
| `overbought_bucket` | `overbought_proxy_normal` | 88 | 88 | 0.4042 | 0.6885 | 0.4886 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 79 | 79 | -0.7871 | -2.758 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 590 | 79 | -0.8121 | -0.289 | 0.3418 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_unknown` | 1403 | 65 | -0.8472 | -0.0602 | 0.4462 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_watch` | 50 | 50 | 0.6136 | 0.9606 | 0.52 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 49 | 49 | 1.5253 | 2.4068 | 0.6122 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_block` | 453 | 37 | -1.4122 | -1.2689 | 0.1081 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 30 | 30 | -0.3388 | -0.0814 | 0.3333 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 20 | 20 | 1.0562 | 1.4859 | 0.55 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1000_1200` | 18 | 18 | -1.0431 | -1.62 | 0.5 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 419 | 18 | -0.9097 | 0.1078 | 0.4444 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 190 | 16 | -1.5448 | -0.9781 | 0.4375 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_chase_risk|time=time_0900_1000` | 16 | 16 | -1.9 | -2.6502 | 0.25 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 113 | 14 | -0.4175 | -0.6071 | 0.2857 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 117 | 13 | -2.1409 | -0.9993 | 0.1538 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 77, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1936 | 1379 | -0.7359 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 1760 | 1326 | -0.7249 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1533 | 1267 | -0.7135 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1614 | 1261 | -0.6574 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1441 | 1212 | -0.6975 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1229 | 991 | -0.6081 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1163 | 948 | -0.5959 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1210 | 921 | -0.7863 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 958 | 794 | -0.711 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `latency_state` | `simulated` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 900 | 645 | -0.735 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 926 | 641 | -0.729 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 896 | 641 | -0.729 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 635 | 624 | -0.6918 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 688 | 541 | -0.667 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 688 | 541 | -0.667 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 688 | 541 | -0.667 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 658 | 541 | -0.667 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 688 | 541 | -0.667 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 550 | 467 | -0.7104 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 549 | 394 | -0.5697 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 365 | 315 | -1.0549 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 267 | 267 | -0.6954 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 291 | 262 | -1.102 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 238 | 238 | -0.5688 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 216 | 153 | -0.5899 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 159 | 142 | -0.9283 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 175 | 112 | -1.0231 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 88 | 80 | -0.6005 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 76 | 59 | -2.1046 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 83 | 57 | -0.9824 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 229 | 57 | -0.9824 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 83 | 57 | -0.9824 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 71 | 53 | -1.0431 | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 183 | 36 | -1.1063 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 37 | 36 | -1.1063 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 40 | 35 | -0.8221 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 28 | 28 | -2.3678 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 23 | 22 | -1.5233 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 68, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_source_stage` | `scalp_sim_holding_started` | 1616 | 1324 | -0.6966 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 1194 | 981 | -0.634 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 1224 | 933 | -0.7421 | `source_quality_workorder` |
| `profit_band` | `profit_lt_neg070` | 710 | 698 | -1.5065 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_not_applicable_at_start` | 392 | 391 | -0.588 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 352 | 352 | -1.4232 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 300 | 191 | -1.0357 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 183 | 161 | -0.2564 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 145 | 145 | -1.5619 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 148 | 143 | 0.1794 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 152 | 131 | -0.305 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 125 | 124 | -0.6099 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 129 | 118 | 0.6169 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 117 | 117 | -0.2858 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 112 | 112 | -1.6508 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 94 | 94 | -0.2449 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 78 | 78 | 0.1385 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 78 | 73 | 1.5346 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 66 | 66 | -1.6457 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 50 | 50 | 0.7429 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 40 | 40 | 0.7206 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 31 | 31 | -0.4683 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 30 | 30 | 1.2815 | `source_quality_workorder` |
| `holding_action` | `BUY` | 42 | 28 | -0.9622 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 27 | 27 | 0.5043 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 26 | 26 | 0.0166 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 19 | 19 | 1.8757 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 19 | 19 | 0.2533 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 17 | 17 | -1.5398 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 17 | 17 | -0.2719 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 15 | 15 | 0.6178 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 1.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 13 | 13 | -0.1877 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.4172 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 10 | 10 | -0.3366 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 8 | 8 | 1.5029 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 6 | 6 | -0.7367 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_unknown` | 3 | 3 | 0.8709 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 3 | 3 | -0.9726 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.0295 | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 116, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 3630 | 3630 | -0.526 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 3630 | 3630 | -0.526 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 4497 | 2967 | -0.4698 | `source_quality_workorder` |
| `profit_band` | `profit_lt_neg070` | 2087 | 2087 | -1.2579 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 1940 | 1940 | -0.4487 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1272 | 1272 | -0.4668 | `source_quality_workorder` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1243 | 1243 | -0.7343 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 987 | 987 | -0.5334 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 941 | 941 | -1.1221 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 634 | 634 | 0.1192 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 472 | 472 | -1.2907 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 414 | 414 | -1.2007 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 407 | 407 | -0.1549 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 401 | 401 | -0.4678 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 389 | 389 | 0.3232 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 364 | 364 | -0.6604 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 344 | 344 | -0.3544 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 334 | 334 | -1.3276 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 323 | 323 | 0.2417 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 291 | 291 | -1.8703 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 248 | 248 | -0.1499 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 244 | 244 | 0.3641 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 232 | 232 | 0.5516 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 206 | 206 | 1.2321 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 131 | 131 | -2.5597 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 118 | 118 | -1.8249 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 118 | 118 | -1.1946 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 114 | 114 | -1.1759 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 110 | 110 | 0.283 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 110 | 110 | -0.4068 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 98 | 98 | 2.0963 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 96 | 96 | -0.8881 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 75 | 75 | -0.3012 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 52 | 52 | -0.0547 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 51 | 51 | 1.1314 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 51 | 51 | -0.3745 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 47 | 47 | 2.0196 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 45 | 45 | -1.6658 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 44 | 44 | -0.7247 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 42 | 42 | 0.7876 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 552, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 193235 | 193050 | -0.5407 | -0.6026 | 0.0808 | `hold_no_edge` |
| `ai_score_source` | `ai_source_unknown` | 168701 | 166834 | -0.2708 | -0.3118 | 0.2592 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 98336 | 98336 | -0.2656 | -0.3036 | 0.2688 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 70428 | 70428 | -0.2062 | -0.2014 | 0.3003 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 70428 | 70428 | -0.2062 | -0.2014 | 0.3003 | `hold_no_edge` |
| `arm` | `arm_unknown` | 70416 | 70416 | -0.2064 | -0.2017 | 0.3002 | `hold_no_edge` |
| `arm` | `PYRAMID` | 61735 | 59814 | 0.6056 | 0.5438 | 0.9228 | `hold_no_edge` |
| `ai_score_source` | `score_field_backfilled` | 43538 | 43538 | -0.1844 | -0.2176 | 0.3055 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 38089 | 38089 | -0.3557 | -0.4221 | 0.2883 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 30106 | 30106 | -0.1752 | -0.197 | 0.2449 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 28574 | 28574 | -0.1896 | -0.2216 | 0.2715 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 27038 | 27038 | -0.3407 | -0.3992 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 20225 | 20225 | -0.2805 | -0.2969 | 0.1637 | `hold_no_edge` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20143 | 20143 | -0.0311 | -0.013 | 0.3573 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `profit_not_enough` | 16483 | 16483 | 0.541 | 0.4877 | 0.9783 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_63_65` | 15255 | 15255 | -0.188 | -0.2168 | 0.2615 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 7481 | 7481 | -0.0295 | -0.1062 | 0.3798 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 4028 | 4028 | -0.1641 | -0.272 | 0.1383 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 3645 | 3645 | -0.3492 | -0.3693 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `near_market_close` | 1940 | 1940 | -0.1278 | -0.1278 | 0.1505 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 1639 | 1639 | -0.298 | -0.3065 | 0.0689 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `lifecycle_decision_matrix_pyramid` | 1510 | 1510 | -0.085 | -0.276 | 0.3437 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 1470 | 1470 | -0.0326 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 887 | 887 | 0.0145 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 804 | 804 | -0.0166 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 790 | 790 | -0.0537 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 664 | 664 | -0.6713 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 605 | 605 | -0.6717 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 565 | 565 | 2.7237 | 2.7318 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 550 | 550 | -0.0242 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 490 | 490 | -0.7306 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 477 | 477 | -0.7703 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.84)` | 476 | 476 | -0.7389 | -0.84 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 476 | 476 | -0.8673 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 461 | 461 | -0.0417 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `ok` | 458 | 458 | -8.7551 | -10.9271 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 456 | 456 | -0.7233 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 456 | 456 | -1.174 | -1.29 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 392 | 392 | -0.8598 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.99)` | 385 | 385 | -0.8957 | -0.99 | 0.0 | `candidate_tighten_or_exclude` |

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
| `overnight_action` | `SELL_TODAY` | 304 | 228 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `stage` | `exit` | 152 | 152 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 228 | 152 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 219 | 146 | 0.3675 | 0.49 | 0.4383 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 152 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `peak_profit_band` | `peak_unknown` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 76 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 142 | 71 | 0.3694 | 0.4925 | 0.4226 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 88 | 44 | -0.3317 | -0.4423 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 66 | 44 | 0.0808 | 0.1077 | 0.5 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 63 | 42 | -0.2311 | -0.3081 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 36 | 24 | -0.7643 | -1.0192 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 22 | 22 | 0.0808 | 0.1077 | 0.5 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 22 | 22 | 0.0808 | 0.1077 | 0.5 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 33 | 22 | 1.6739 | 2.2318 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 21 | 21 | -0.2311 | -0.3081 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 21 | 21 | -0.2311 | -0.3081 | 0.0 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 22 | 11 | 0.2134 | 0.2845 | 1.0 | `hold_no_edge` |

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
