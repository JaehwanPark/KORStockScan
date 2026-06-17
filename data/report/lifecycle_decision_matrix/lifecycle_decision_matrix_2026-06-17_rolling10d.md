# Lifecycle Decision Matrix - 2026-06-17

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-17_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `172802`
- source_rows_total: `249076`
- retained_rows: `172802`
- dropped_rows_by_source: `{}`
- joined_rows: `158048`
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
- lifecycle_flow_bucket_count: `672`
- lifecycle_flow_complete_count: `829`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0052`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 8617 | 1274 | 0.5726 | 0.9743 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 3378 | 2261 | -0.5366 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 3157 | 2261 | -0.9288 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 150506 | 148563 | -0.4214 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 7144 | 3689 | -0.9579 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 672, 'complete_flow_count': 829, 'incomplete_flow_count': 157220, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 115255 | 114669 | -0.7345 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 33686 | 32329 | 0.7082 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 1314 | 1314 | -1.0757 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 259 | 259 | 1.4671 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 225 | 225 | 1.5368 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 153 | 153 | 1.4225 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 114 | 114 | -0.2557 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 37 | 37 | -0.9232 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 27 | 27 | -0.8685 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 21 | 21 | -0.991 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 19 | 19 | -1.3559 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:8050d08a3f` | 17 | 17 | -2.0005 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 17 | 17 | -1.2023 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9d8cac316e` | 12 | 12 | -0.4818 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:67138f9e63` | 12 | 12 | -0.9026 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3cbb81cd02` | 10 | 10 | -0.8689 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 10 | 10 | -0.315 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:89e49a11bc` | 9 | 9 | -1.2942 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:9b100ebd9b` | 9 | 9 | -1.1942 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:81b7841fa7` | 9 | 9 | -1.227 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 409, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 5925 | 1270 | 0.5746 | 0.6367 | 0.4583 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 5669 | 929 | 0.5253 | 0.241 | 0.4424 | `hold_no_edge` |
| `chosen_action` | `WAIT_REQUOTE` | 641 | 641 | 1.4714 | 2.3838 | 0.6537 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 7984 | 641 | 1.4714 | 2.3838 | 0.6537 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 6169 | 589 | -0.316 | -1.2125 | 0.2462 | `hold_no_edge` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 3350 | 462 | -0.3531 | -1.2121 | 0.2467 | `hold_no_edge` |
| `stale_bucket` | `fresh` | 3861 | 461 | -0.3529 | -1.217 | 0.2451 | `hold_no_edge` |
| `strength_bucket` | `weak_strength_momentum` | 3613 | 454 | -0.2146 | -0.9726 | 0.2797 | `hold_no_edge` |
| `stale_bucket` | `fresh_or_unflagged` | 1638 | 394 | 0.8999 | 1.5409 | 0.6142 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 394 | 394 | 0.8999 | 1.5409 | 0.6142 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 777 | 363 | 0.8102 | 1.3325 | 0.5841 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 1566 | 308 | 0.229 | 0.0651 | 0.4448 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 296 | 296 | -0.2405 | -1.9799 | 0.0 | `hold_no_edge` |
| `score_band` | `score_60_62` | 3371 | 289 | -0.367 | -1.2949 | 0.2249 | `hold_no_edge` |
| `score_band` | `score_70p` | 563 | 242 | 0.733 | 1.4336 | 0.6074 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 1174 | 211 | 0.4836 | 0.3962 | 0.436 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 737 | 167 | 1.0271 | 1.257 | 0.4851 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 311 | 164 | 0.9056 | 1.2443 | 0.5732 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 160 | 160 | -0.5831 | 1.9898 | 1.0 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 150 | 150 | -0.3689 | -2.9304 | 0.0 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_ok` | 514 | 148 | 0.2219 | 1.8946 | 0.5203 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 1245 | 147 | -0.4474 | -0.8937 | 0.2993 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 581 | 139 | 0.2734 | 0.3506 | 0.4389 | `hold_no_edge` |
| `time_bucket` | `time_1400_close` | 396 | 50 | -0.8885 | -1.4996 | 0.24 | `hold_no_edge` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 120, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 3267 | 2261 | -0.5366 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 2997 | 2261 | -0.5366 | `keep_collecting` |
| `latency_state` | `simulated` | 2997 | 2261 | -0.5366 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 3263 | 2261 | -0.5366 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 2956 | 2230 | -0.52 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 2746 | 2085 | -0.5627 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 2436 | 1845 | -0.5601 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2406 | 1807 | -0.5912 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1813 | 1380 | -0.6853 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 1713 | 1305 | -0.5759 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1673 | 1288 | -0.6719 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1564 | 1288 | -0.6719 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1564 | 1288 | -0.6719 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1597 | 1241 | -0.6297 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 1401 | 973 | -0.3575 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 1401 | 973 | -0.3575 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 1201 | 891 | -0.3747 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1130 | 781 | -0.3387 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 981 | 770 | -0.5504 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 918 | 696 | -0.3202 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 844 | 674 | -0.7572 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 716 | 490 | -0.3309 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 573 | 423 | -0.2161 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 561 | 416 | -0.4326 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 286 | 238 | -0.5959 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 321 | 210 | -0.4271 | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 181 | 181 | -0.3372 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 251 | 176 | -0.2284 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 664 | 176 | -0.2284 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 251 | 176 | -0.2284 | `keep_collecting` |
| `would_limit_fill` | `false` | 631 | 175 | -0.23 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 198 | 171 | -0.3117 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|fill=false|submitted=false` | 212 | 142 | -0.0763 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 196 | 127 | -0.7704 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 57 | 57 | -0.5425 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 47, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 2997 | 2261 | -0.9288 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2997 | 2261 | -0.9288 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 1737 | 1677 | -1.4346 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1863 | 1399 | -1.033 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1047 | 1047 | -1.5129 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 967 | 726 | -0.7023 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 513 | 513 | -1.2762 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 202 | 189 | 0.2338 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 154 | 148 | 0.5468 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 167 | 136 | -1.0658 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 117 | 117 | -1.428 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 154 | 116 | 0.0537 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 115 | 115 | 0.1139 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 94 | 91 | 2.0791 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 86 | 86 | 0.0224 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 84 | 84 | 0.4385 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 72 | 72 | 0.4089 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 53 | 53 | 0.6692 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 46 | 46 | 2.0462 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 80 | 40 | -0.3697 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 40 | 40 | 2.1122 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 29 | 29 | 0.1048 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 21 | 21 | -0.3381 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 19 | 19 | -0.4046 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 11 | 11 | 0.7844 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 5 | 5 | 2.1165 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8266 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 1.2647 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 160 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 47 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 113 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 736 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 160 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 31 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 241 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 464 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 16 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 44 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 26 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 72, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 2777 | 2777 | -1.3364 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 1978 | 1978 | -0.9832 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1551 | 1551 | -1.0069 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1551 | 1551 | -1.0069 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1551 | 1551 | -1.0069 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 1195 | 1195 | -1.2096 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 857 | 857 | -1.2785 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 758 | 758 | -1.4859 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 699 | 699 | -0.5184 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 586 | 586 | -1.8253 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 521 | 521 | -0.8756 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 445 | 445 | 0.5746 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 360 | 360 | -0.5103 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 315 | 315 | -0.5406 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 307 | 307 | -1.6852 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 291 | 291 | -1.1806 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 259 | 259 | -0.9063 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 253 | 253 | -1.2922 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 246 | 246 | -2.4107 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 173 | 173 | 0.2704 | `hold_no_edge` |
| `exit_outcome` | `outcome_unknown` | 3615 | 160 | -0.1696 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 160 | 160 | -0.1696 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 160 | 160 | -0.1696 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg010_pos080` | 145 | 145 | 0.0937 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 143 | 143 | 0.6471 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 91 | 91 | 2.2881 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 87 | 87 | -1.7204 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 84 | 84 | -0.4953 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 62 | 62 | 0.0627 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 60 | 60 | -1.0084 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 57 | 57 | -0.3469 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 49 | 49 | 0.2822 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 48 | 48 | 1.0877 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 45 | 45 | 0.779 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300_plus` | 41 | 41 | 2.3685 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 40 | 40 | -0.292 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 39 | 39 | -0.4419 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg010_pos080` | 38 | 38 | 0.2698 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 32 | 32 | 1.1431 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 29 | 29 | -0.5257 | `candidate_tighten_or_exclude` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 513, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 148530 | 148530 | None | -0.4922 | 0.2141 | `hold_sample` |
| `arm` | `AVG_DOWN` | 116695 | 116109 | None | -0.81 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 85346 | 85346 | None | -0.4944 | 0.2105 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 81867 | 81281 | None | -0.9759 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 34828 | 34828 | None | -0.4228 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 33811 | 32454 | None | 0.6462 | 0.9805 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 33811 | 32454 | None | 0.6462 | 0.9805 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 27666 | 27666 | None | 0.5242 | 0.9833 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 25522 | 25522 | None | -0.4384 | 0.2357 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 20564 | 20564 | None | -0.5131 | 0.2107 | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 13327 | 13327 | None | -0.3271 | 0.1622 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 9074 | 9074 | None | -0.5131 | 0.2084 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 8024 | 8024 | None | -0.5624 | 0.1983 | `hold_sample` |
| `blocker_reason` | `low_broken` | 3173 | 3173 | None | -0.4636 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 1762 | 1762 | None | -0.845 | 0.0834 | `hold_sample` |
| `blocker_reason` | `ok` | 1281 | 1281 | None | -2.3609 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 1266 | 1266 | None | -0.96 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 1251 | 1251 | None | -1.2 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.10)` | 1249 | 1249 | None | -1.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 1240 | 1240 | None | 3.2454 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 320 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `overnight_status` | `SELL_TODAY` | 160 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 320 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 160 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 320 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 320 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 160 | 160 | -0.1696 | -0.2261 | 0.35 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 226 | 113 | -0.164 | -0.2187 | 0.3628 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 208 | 104 | -0.6956 | -0.9274 | 0.0 | `candidate_tighten_or_exclude` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 60 | 60 | -1.0084 | -1.3445 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 120 | 60 | -1.0084 | -1.3445 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 94 | 47 | -0.183 | -0.244 | 0.3192 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 40 | 40 | -0.292 | -0.3893 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 80 | 40 | -0.292 | -0.3893 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 38 | 38 | 0.2698 | 0.3597 | 0.8947 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 76 | 38 | 0.2698 | 0.3597 | 0.8947 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 68 | 34 | 0.3062 | 0.4082 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 13 | 13 | 0.8521 | 1.1362 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 26 | 13 | 0.8521 | 1.1362 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 26 | 13 | 0.8521 | 1.1362 | 1.0 | `hold_sample` |

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
