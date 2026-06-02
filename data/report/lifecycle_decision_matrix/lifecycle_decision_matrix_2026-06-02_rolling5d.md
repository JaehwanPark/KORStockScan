# Lifecycle Decision Matrix - 2026-06-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-06-02_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `69115`
- source_rows_total: `105745`
- retained_rows: `69115`
- dropped_rows_by_source: `{}`
- joined_rows: `66183`
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
- lifecycle_flow_bucket_count: `278`
- lifecycle_flow_complete_count: `302`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0056`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2336 | 498 | 1.6192 | 1.0 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 1016 | 905 | -0.5191 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 965 | 905 | -0.7649 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 61912 | 61898 | -0.226 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 2886 | 1977 | -0.7669 | 1.0 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 278, 'complete_flow_count': 302, 'incomplete_flow_count': 54097, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 38264 | 38258 | -0.6586 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 12744 | 12740 | 0.6544 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 681 | 681 | -0.9833 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 202 | 202 | 2.1109 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 150 | 150 | 2.4313 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 46 | 46 | -0.1685 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 33 | 33 | 1.558 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:93f13405b3` | 12 | 12 | -0.9184 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 12 | 12 | -0.6758 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:07dd4b972c` | 11 | 11 | -0.5823 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:7c897ec6ef` | 9 | 9 | -2.2716 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b72b8d0720` | 8 | 8 | -1.5616 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:438a0575a6` | 8 | 8 | -0.2371 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:0e963d335b` | 8 | 8 | -0.7238 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 8 | 8 | -0.7987 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:3799fc10bf` | 7 | 7 | -0.6467 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:1905c4a9b7` | 5 | 5 | 1.2181 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:92237a65fa` | 5 | 5 | -0.4185 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:cbc2ec64ca` | 4 | 4 | 0.6865 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_bl:b85b2fccd5` | 4 | 4 | 2.7842 | `candidate_recovery_or_relax` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 250, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 385 | 385 | 2.1883 | 3.503 | 0.6156 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2223 | 385 | 2.1883 | 3.503 | 0.6156 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 1267 | 385 | 2.1883 | 3.503 | 0.6156 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 385 | 385 | 2.1883 | 3.503 | 0.6156 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 385 | 385 | 2.1883 | 3.503 | 0.6156 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 403 | 318 | 2.1716 | 3.4926 | 0.6164 | `candidate_recovery_or_relax` |
| `score_band` | `score_70p` | 594 | 231 | 1.7735 | 3.0049 | 0.6191 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_proxy_normal` | 204 | 204 | 2.114 | 3.2788 | 0.6079 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 222 | 156 | 2.352 | 3.7022 | 0.5769 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 1069 | 113 | -0.3198 | -0.5923 | 0.4071 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 722 | 113 | -0.3198 | -0.5923 | 0.4071 | `candidate_tighten_or_exclude` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 722 | 113 | -0.3198 | -0.5923 | 0.4071 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh` | 815 | 110 | -0.3151 | -0.5443 | 0.4182 | `candidate_tighten_or_exclude` |
| `overbought_bucket` | `overbought_proxy_watch` | 104 | 104 | 2.2342 | 3.6469 | 0.6346 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 460 | 100 | 2.0434 | 3.2087 | 0.66 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 647 | 99 | -0.2152 | -0.4684 | 0.4343 | `candidate_tighten_or_exclude` |
| `chosen_action` | `NO_BUY_AI` | 1028 | 87 | -0.2408 | -0.776 | 0.3563 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_1200_1400` | 377 | 79 | 1.7521 | 2.8912 | 0.6709 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 1116 | 52 | -0.387 | -1.0166 | 0.3269 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 172 | 51 | 1.922 | 3.0431 | 0.5686 | `hold_sample` |
| `overbought_bucket` | `overbought_proxy_chase_risk` | 48 | 48 | 2.1038 | 3.4472 | 0.6041 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 46 | 46 | -0.0309 | 1.6809 | 1.0 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_normal|time=time_1200_1400` | 42 | 42 | 2.1856 | 3.4339 | 0.5476 | `hold_no_edge` |
| `time_bucket` | `time_0900_1000` | 197 | 33 | 0.0537 | 0.1545 | 0.4242 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_proxy_watch|time=time_1000_1200` | 31 | 31 | 1.7467 | 2.8387 | 0.7097 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 73, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_guard_action` | `would_pass` | 1099 | 1082 | -0.5187 | `keep_collecting` |
| `actual_order_submitted` | `false` | 1133 | 923 | -0.5273 | `keep_collecting` |
| `actual_order_submitted` | `true` | 1017 | 908 | -0.5225 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 919 | 905 | -0.5191 | `keep_collecting` |
| `latency_state` | `simulated` | 919 | 905 | -0.5191 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 898 | 884 | -0.5071 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 929 | 854 | -0.4213 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 795 | 782 | -0.494 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 739 | 728 | -0.5197 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 767 | 727 | -0.5182 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 738 | 727 | -0.5182 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 578 | 569 | -0.4303 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 531 | 524 | -0.5674 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 503 | 495 | -0.3647 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 393 | 387 | -0.6856 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 357 | 351 | -0.4132 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 314 | 310 | -0.6681 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 309 | 305 | -0.4706 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 303 | 297 | -0.3475 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_ok` | 181 | 178 | -0.5233 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 159 | 156 | -0.4484 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 124 | 123 | -0.6788 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 99 | 96 | -0.3635 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 90 | 90 | -0.4237 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 60 | 50 | -2.1672 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 39 | 39 | -0.4227 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 27 | 26 | -0.6863 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 21 | 21 | -1.0249 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 119 | 21 | -1.0249 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 21 | 21 | -1.0249 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=false|submitted=false` | 16 | 16 | -1.0255 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -0.8555 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 13 | 13 | -3.6922 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 8 | 8 | -1.876 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -1.4741 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_lt1s` | 6 | 6 | -0.6541 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | -3.3178 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_lt1s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_unknown|latency=simulated|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.0876 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 3 | 3 | -0.6866 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_unknown|latency=simulated|fill=true|submitted=false` | 3 | 3 | -1.5309 | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 919 | 905 | -0.7649 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 919 | 905 | -0.7649 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 611 | 598 | -1.4386 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 578 | 569 | -0.6958 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 368 | 368 | -1.3689 | `candidate_tighten_or_exclude` |
| `holding_action` | `holding_action_not_applicable_at_start` | 323 | 318 | -0.8862 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 215 | 215 | -1.5632 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 91 | 88 | 0.1215 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 93 | 83 | 0.0233 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 78 | 73 | 0.905 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 58 | 58 | 0.0823 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 52 | 52 | 0.9581 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 51 | 51 | 0.0952 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 52 | 50 | 1.8843 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 35 | 35 | 0.064 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 31 | 31 | 1.6694 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 25 | 25 | -0.1137 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 21 | 21 | 0.7737 | `candidate_recovery_or_relax` |
| `holding_action` | `BUY` | 18 | 18 | -0.8086 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 18 | 18 | 2.2315 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 15 | 15 | -1.3631 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 26 | 13 | -0.3735 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 9 | 9 | -0.3672 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 4 | 4 | -0.3875 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 1.799 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.2951 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 46 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 18 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 28 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 14 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 46 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 10 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg010_pos080|held=held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 9 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 80, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 1234 | 1234 | -1.3208 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 1062 | 1062 | -0.7834 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 1062 | 1062 | -0.7834 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 1062 | 1062 | -0.7834 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 854 | 854 | -0.8193 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 635 | 635 | -1.219 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 353 | 353 | -1.3686 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 344 | 344 | -0.4789 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 327 | 327 | -0.4901 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 305 | 305 | -0.2223 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 293 | 293 | -1.2342 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 271 | 271 | -1.7531 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 262 | 262 | 0.5186 | `candidate_recovery_or_relax` |
| `exit_outcome` | `NEUTRAL` | 196 | 196 | -0.7588 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 145 | 145 | 0.1433 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 127 | 127 | -2.3571 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 107 | 107 | 0.2136 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 106 | 106 | 0.2907 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 106 | 106 | -1.6478 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 104 | 104 | -1.0836 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 97 | 97 | -0.8648 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 91 | 91 | 1.1624 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 89 | 89 | -1.1573 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 970 | 61 | 0.2548 | `source_quality_workorder` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 61 | 61 | 0.3133 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300_plus` | 57 | 57 | 2.1256 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 40 | 40 | -1.5765 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 36 | 36 | -0.546 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 32 | 32 | 0.8192 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 27 | 27 | -0.5107 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 26 | 26 | 0.1121 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 26 | 26 | 1.4795 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 24 | 24 | 1.0261 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 23 | 23 | 0.6011 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 20 | 20 | -0.0225 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 18 | 18 | -0.2826 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos150_pos300` | 17 | 17 | 2.3171 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos080_pos150` | 17 | 17 | 0.0685 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 16 | 16 | 1.2082 | `candidate_recovery_or_relax` |
| `exit_source_stage` | `scalp_sim_sell_order_assumed_filled` | 15 | 15 | 0.5485 | `candidate_recovery_or_relax` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 291, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `arm` | `AVG_DOWN` | 76003 | 75991 | -0.7276 | -0.7916 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `score_field_backfilled` | 61898 | 61898 | -0.226 | -0.2762 | 0.2815 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 35741 | 35741 | -0.1444 | -0.1931 | 0.3244 | `hold_no_edge` |
| `arm` | `PYRAMID` | 35404 | 35388 | 0.8974 | 0.8792 | 0.9846 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 12417 | 12417 | -0.3576 | -0.4148 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 10972 | 10972 | 0.2543 | 0.2844 | 0.4478 | `candidate_recovery_or_relax` |
| `blocker_reason` | `profit_not_enough` | 10361 | 10361 | 0.601 | 0.5492 | 0.9885 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 10060 | 10060 | -0.3055 | -0.3532 | 0.2306 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 8142 | 8142 | -0.265 | -0.285 | 0.2026 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 7858 | 7858 | -0.394 | -0.4435 | 0.1943 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 4561 | 4561 | -0.3469 | -0.4139 | 0.2392 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 3678 | 3678 | -0.2918 | -0.3447 | 0.2417 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 1800 | 1800 | -0.4019 | -0.4301 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 533 | 533 | 2.5734 | 2.5716 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 412 | 412 | -1.8796 | -2.3606 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 369 | 369 | -0.8601 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.77)` | 317 | 317 | -0.6991 | -0.77 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_cutoff` | 315 | 315 | -0.1728 | -0.1925 | 0.2412 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 305 | 305 | -0.6801 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.79)` | 292 | 292 | -0.7273 | -0.79 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 282 | 282 | -1.0722 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.81)` | 272 | 272 | -0.7349 | -0.81 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.27)` | 257 | 257 | -1.184 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.78)` | 249 | 249 | -0.6966 | -0.78 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 244 | 244 | -0.0114 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.06)` | 242 | 242 | -0.9609 | -1.06 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 237 | 237 | -0.6592 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 235 | 235 | -0.7651 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.86)` | 233 | 233 | -0.7725 | -0.86 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.09)` | 228 | 228 | -0.9749 | -1.09 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.80)` | 216 | 216 | -0.7268 | -0.8 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 214 | 214 | -0.7332 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 210 | 210 | -0.6539 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.87)` | 210 | 210 | -0.7812 | -0.87 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 208 | 208 | -0.8212 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.02)` | 206 | 206 | 0.029 | -0.02 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 206 | 206 | -0.0349 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 206 | 206 | -0.881 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 201 | 201 | -0.6229 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 199 | 199 | -0.8434 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 45, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 153 | 107 | 0.2136 | 0.2848 | 0.4019 | `candidate_recovery_or_relax` |
| `stage` | `exit` | 61 | 61 | 0.2548 | 0.3397 | 0.4098 | `candidate_recovery_or_relax` |
| `price_source` | `holding_price_samples_last` | 107 | 61 | 0.2548 | 0.3397 | 0.4098 | `candidate_recovery_or_relax` |
| `source_quality_gate` | `overnight_decision_coverage` | 107 | 61 | 0.2548 | 0.3397 | 0.4098 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_070p` | 92 | 46 | 0.159 | 0.212 | 0.3913 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 46 | 46 | 0.159 | 0.212 | 0.3913 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s_plus` | 56 | 28 | 0.2518 | 0.3357 | 0.4286 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_lt_zero` | 54 | 27 | -0.5089 | -0.6785 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 36 | 18 | 0.0146 | 0.0195 | 0.3333 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 30 | 17 | -0.7716 | -1.0288 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 29 | 16 | -0.262 | -0.3494 | 0.0 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `confidence_band` | `confidence_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `peak_profit_band` | `peak_unknown` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 15 | 15 | 0.5485 | 0.7313 | 0.4667 | `candidate_recovery_or_relax` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 13 | 13 | -0.7748 | -1.0331 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 13 | 13 | -0.2787 | -0.3715 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 22 | 12 | 0.1375 | 0.1833 | 0.75 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 10 | 10 | 0.1418 | 0.189 | 0.8 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 13 | 8 | 1.7691 | 2.3588 | 1.0 | `candidate_recovery_or_relax` |

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
