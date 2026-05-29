# Lifecycle Decision Matrix - 2026-05-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-29_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `252969`
- source_rows_total: `252969`
- retained_rows: `252969`
- dropped_rows_by_source: `{}`
- joined_rows: `240062`
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
- lifecycle_flow_bucket_count: `306`
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
| `entry` | 7667 | 839 | -0.0728 | 0.9186 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1884 | 1437 | -0.717 | 0.9928 | `pass` | `NO_CHANGE` | False |
| `holding` | 1838 | 1437 | -0.6771 | 0.9933 | `pass` | `EXIT` | False |
| `scale_in` | 234738 | 231037 | -0.2884 | 0.9999 | `pass` | `NO_CHANGE` | False |
| `exit` | 6842 | 5312 | -0.5435 | 0.9994 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 306, 'complete_flow_count': 165, 'incomplete_flow_count': 24150, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 110700 | 110389 | -0.3947 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 24192 | 22208 | 0.5315 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:71610cf3d7` | 323 | 323 | -0.4399 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:bfc859574f` | 1795 | 265 | -0.7216 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:5f8bb8e981` | 260 | 260 | -0.4312 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 257 | 257 | -0.6021 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 99 | 99 | 0.4783 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:e81b5f597d` | 94 | 94 | -0.3934 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bf81e4fab9` | 83 | 83 | -0.4989 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:9f284741cf` | 76 | 76 | 2.6587 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 63 | 63 | 0.3689 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a9fa2e4711` | 1052 | 59 | -0.8086 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:63acce4470` | 53 | 53 | -0.1351 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:0dbddcc72e` | 49 | 49 | 1.5253 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:6f3404e612` | 348 | 46 | -0.1868 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 46 | 46 | -0.1122 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:66ac2828ed` | 44 | 44 | -0.2634 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ab1924a1fc` | 112 | 33 | -1.5549 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4690e15525` | 166 | 27 | -0.8248 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d674cba11b` | 242 | 26 | -1.481 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 328, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_unknown` | 7128 | 662 | -0.1978 | 0.3914 | 0.4335 | `hold_sample` |
| `overbought_bucket` | `overbought_unknown` | 5785 | 646 | -0.1644 | 0.4253 | 0.4334 | `hold_sample` |
| `strength_bucket` | `risk_unknown` | 4397 | 532 | -0.7982 | -0.4069 | 0.3872 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 4388 | 526 | -0.7933 | -0.4098 | 0.3878 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 5429 | 481 | -0.7502 | -0.3973 | 0.3825 | `hold_sample` |
| `stale_bucket` | `fresh` | 3462 | 417 | -0.7229 | -0.3977 | 0.3981 | `hold_sample` |
| `score_band` | `score_60_62` | 3943 | 314 | -0.7754 | -0.4525 | 0.3694 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 7135 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 2139 | 307 | 1.1842 | 1.9857 | 0.5342 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 307 | 307 | 1.1842 | 1.9857 | 0.5342 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 1738 | 258 | -0.3235 | -0.3845 | 0.438 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 2073 | 237 | -0.7013 | -0.1076 | 0.3966 | `hold_sample` |
| `score_band` | `score_70p` | 822 | 223 | 0.8456 | 1.7797 | 0.5247 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 1732 | 189 | -0.7692 | -0.228 | 0.3598 | `candidate_tighten_or_exclude` |
| `chosen_action` | `WAIT_REQUOTE` | 184 | 177 | 0.3944 | 0.7571 | 0.4689 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 177 | 177 | 0.3944 | 0.7571 | 0.4689 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 169 | 169 | -1.0674 | 1.7556 | 1.0 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strong_strength_momentum` | 593 | 152 | 0.4135 | 0.8156 | 0.454 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 137 | 137 | -0.858 | -1.8866 | 0.0073 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 1600 | 130 | 2.2594 | 3.6585 | 0.6231 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 126 | 126 | -0.4229 | -0.3388 | 0.2064 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_normal` | 88 | 88 | 0.4042 | 0.6885 | 0.4886 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 79 | 79 | -0.7871 | -2.758 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 590 | 79 | -0.8121 | -0.289 | 0.3418 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 76 | 76 | 2.6587 | 4.3494 | 0.6316 | `candidate_recovery_or_relax` |
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
- summary: `{'bucket_count': 82, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 2091 | 1503 | -0.7296 | `keep_collecting` |
| `would_limit_fill` | `true` | 1871 | 1421 | -0.7198 | `keep_collecting` |
| `overbought_bucket` | `overbought_unknown` | 1755 | 1374 | -0.6546 | `source_quality_workorder` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1644 | 1369 | -0.7033 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1535 | 1306 | -0.6965 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1315 | 1077 | -0.6118 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 1248 | 1033 | -0.6027 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1210 | 921 | -0.7863 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1030 | 866 | -0.7007 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `latency_state` | `simulated` | 1055 | 783 | -0.7652 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 729 | 718 | -0.6907 | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 829 | 654 | -0.6593 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 829 | 654 | -0.6593 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 829 | 654 | -0.6593 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 799 | 654 | -0.6593 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 829 | 654 | -0.6593 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 900 | 645 | -0.735 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 926 | 641 | -0.729 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 896 | 641 | -0.729 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 571 | 488 | -0.7234 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 549 | 394 | -0.5697 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 339 | 339 | -0.6726 | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 374 | 324 | -1.0458 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 298 | 269 | -1.0904 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 259 | 259 | -0.6049 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 216 | 153 | -0.5899 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 159 | 142 | -0.9283 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 222 | 131 | -0.9214 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 88 | 80 | -0.6005 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 130 | 76 | -0.8172 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 276 | 76 | -0.8172 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 122 | 76 | -0.8172 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 76 | 59 | -2.1046 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 230 | 55 | -0.8352 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 71 | 53 | -1.0431 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 51 | 47 | -1.0922 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 41 | 36 | -0.892 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 28 | 28 | -2.3678 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 23 | 22 | -1.5233 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 70, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_source_stage` | `scalp_sim_holding_started` | 1749 | 1437 | -0.6771 | `hold_sample` |
| `holding_action` | `WAIT` | 1283 | 1070 | -0.6132 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_unknown` | 1357 | 1046 | -0.7104 | `source_quality_workorder` |
| `profit_band` | `profit_lt_neg070` | 765 | 749 | -1.4995 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 392 | 391 | -0.588 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_unknown` | 391 | 391 | -1.4049 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 356 | 214 | -0.9912 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 208 | 181 | -0.1966 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 171 | 165 | 0.1959 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 145 | 145 | -1.5619 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 158 | 134 | -0.3087 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 140 | 129 | 0.6112 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 125 | 124 | -0.6099 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 124 | 124 | -1.6783 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_unknown` | 119 | 119 | -0.2889 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_unknown` | 110 | 110 | -0.1732 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_unknown` | 98 | 98 | 0.1559 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 84 | 79 | 1.4673 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 66 | 66 | -1.6457 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_unknown` | 57 | 57 | 0.7097 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 40 | 40 | 0.7206 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_unknown` | 35 | 35 | 1.1935 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 35 | 35 | -0.3657 | `source_quality_workorder` |
| `holding_action` | `BUY` | 43 | 29 | -1.0033 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 27 | 27 | 0.5043 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 26 | 26 | 0.0166 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 19 | 19 | 1.8757 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 19 | 19 | 0.2533 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos080_pos150|held=held_unknown` | 19 | 19 | -0.1275 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_unknown` | 17 | 17 | -1.5398 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300|held=held_unknown` | 16 | 16 | 0.1534 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 15 | 15 | 0.6178 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 13 | 13 | 1.7927 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg070_neg010|held=held_unknown` | 11 | 11 | -0.3487 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 10 | 10 | -0.4172 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_pos150_pos300_plus|held=held_unknown` | 9 | 9 | 1.3987 | `source_quality_workorder` |
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
| `exit_outcome` | `outcome_unknown` | 4523 | 2993 | -0.4675 | `source_quality_workorder` |
| `profit_band` | `profit_lt_neg070` | 2139 | 2139 | -1.2589 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1946 | 1946 | -0.4484 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1332 | 1332 | -0.7217 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 1272 | 1272 | -0.4668 | `source_quality_workorder` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 987 | 987 | -0.5334 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_lt_neg070` | 941 | 941 | -1.1221 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 655 | 655 | 0.1227 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 499 | 499 | -1.2634 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 441 | 441 | -0.1689 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 434 | 434 | 0.3168 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 414 | 414 | -1.2007 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 401 | 401 | -0.4678 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 392 | 392 | -0.6542 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 367 | 367 | -1.3114 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 344 | 344 | -0.3544 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_neg010_pos080` | 323 | 323 | 0.2417 | `source_quality_workorder` |
| `exit_rule` | `scalp_hard_stop_pct` | 302 | 302 | -1.877 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 283 | 283 | 0.2858 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 261 | 261 | -0.1526 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 253 | 253 | 0.5251 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 215 | 215 | 1.1899 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 136 | 136 | -2.5467 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 130 | 130 | -1.1789 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 124 | 124 | -1.8355 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 118 | 118 | -1.2009 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 111 | 111 | -0.8882 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 110 | 110 | 0.283 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_full_exit|outcome=outcome_unknown|profit=profit_neg070_neg010` | 110 | 110 | -0.4068 | `source_quality_workorder` |
| `profit_band` | `profit_pos150_pos300_plus` | 104 | 104 | 2.0128 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_panic_lifecycle_full_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 75 | 75 | -0.3012 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 56 | 56 | -0.3519 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 56 | 56 | -0.0715 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos080_pos150` | 51 | 51 | 1.1314 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 50 | 50 | 0.7522 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_unknown|profit=profit_pos150_pos300` | 47 | 47 | 2.0196 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 47 | 47 | -1.6782 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 45 | 45 | -0.7099 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 1096, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 232353 | 231089 | -0.5331 | -0.6059 | 0.1134 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `ai_source_unknown` | 191152 | 187498 | -0.3126 | -0.3679 | 0.2611 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 105453 | 105453 | -0.2463 | -0.2837 | 0.2749 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 70443 | 70443 | -0.203 | -0.1976 | 0.3005 | `candidate_recovery_or_relax` |
| `blocker_reason` | `blocker_reason_unknown` | 70443 | 70443 | -0.203 | -0.1976 | 0.3005 | `candidate_recovery_or_relax` |
| `arm` | `arm_unknown` | 70416 | 70416 | -0.2064 | -0.2017 | 0.3002 | `hold_no_edge` |
| `arm` | `PYRAMID` | 63388 | 60759 | 0.4752 | 0.3768 | 0.9218 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 44611 | 44611 | -0.5947 | -0.7218 | 0.2791 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 43538 | 43538 | -0.1844 | -0.2176 | 0.3055 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 32238 | 32238 | -0.1763 | -0.1995 | 0.2452 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 31590 | 31590 | -0.1782 | -0.2096 | 0.2659 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 29367 | 29367 | -0.3443 | -0.3981 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 24089 | 24089 | -0.2862 | -0.3 | 0.1552 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 20143 | 20143 | -0.0311 | -0.013 | 0.3573 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 17117 | 17117 | -0.1788 | -0.2088 | 0.2625 | `hold_no_edge` |
| `blocker_reason` | `profit_not_enough` | 16483 | 16483 | 0.541 | 0.4877 | 0.9783 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scale_in_probe_blocked` | 11756 | 11756 | -0.0786 | -0.176 | 0.3678 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 7666 | 7666 | -0.1343 | -0.2525 | 0.1776 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 3743 | 3743 | -0.3504 | -0.3699 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `near_market_close` | 2720 | 2720 | -0.0805 | -0.0805 | 0.2758 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 1986 | 1986 | -0.3001 | -0.3071 | 0.079 | `hold_no_edge` |
| `price_guard_reason` | `price_guard_none` | 2102 | 1940 | -5.0195 | -6.2563 | 0.1866 | `candidate_tighten_or_exclude` |
| `qty_reason` | `qty_none` | 2029 | 1940 | -5.0195 | -6.2563 | 0.1866 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_unknown` | 2191 | 1940 | -5.0195 | -6.2563 | 0.1866 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 3048 | 1732 | -0.2536 | -0.2536 | 0.2748 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 1610 | 1610 | -0.0475 | -0.1336 | 0.4 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 1529 | 1529 | -0.0344 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `lifecycle_decision_matrix_pyramid` | 1510 | 1510 | -0.085 | -0.276 | 0.3437 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 916 | 916 | 0.0118 | -0.07 | 0.0 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1145 | 894 | -10.4934 | -13.1772 | 0.1644 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 759 | 759 | -0.3251 | -0.3773 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 692 | 692 | -0.6741 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 633 | 633 | -0.3292 | -0.3931 | 0.1911 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 621 | 621 | -15.5462 | -19.3271 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 565 | 565 | 2.7237 | 2.7318 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `scalping_pyramid_ok` | 563 | 563 | 3.6823 | 4.0098 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 518 | 518 | -0.0437 | -0.06 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 503 | 503 | 0.1732 | 0.151 | 0.6064 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 487 | 487 | -0.8694 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 478 | 478 | 0.2055 | -0.0352 | 0.4352 | `candidate_recovery_or_relax` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 57, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 356 | 267 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `stage` | `exit` | 178 | 178 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 258 | 172 | 0.2812 | 0.3749 | 0.4302 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 228 | 152 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `peak_profit_band` | `peak_unknown` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 89 | 89 | 0.2659 | 0.3545 | 0.4157 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 168 | 84 | 0.2807 | 0.3743 | 0.4167 | `hold_no_edge` |
| `confidence_band` | `confidence_070p` | 152 | 76 | 0.3462 | 0.4616 | 0.421 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 81 | 54 | 0.1144 | 0.1526 | 0.5556 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 104 | 52 | -0.3691 | -0.4921 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 72 | 48 | -0.2462 | -0.3283 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 48 | 32 | -0.7931 | -1.0575 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 27 | 27 | 0.1144 | 0.1526 | 0.5556 | `hold_no_edge` |
| `source_quality_gate` | `source_quality_unknown` | 39 | 26 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 24 | 24 | -0.2462 | -0.3283 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 22 | 22 | 0.0808 | 0.1077 | 0.5 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 21 | 21 | -0.2311 | -0.3081 | 0.0 | `hold_no_edge` |
| `confidence_band` | `confidence_lt040` | 26 | 13 | -0.2037 | -0.2715 | 0.3846 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_lt040|profit=profit_neg010_pos080` | 5 | 5 | 0.2625 | 0.35 | 0.8 | `hold_no_edge` |

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
