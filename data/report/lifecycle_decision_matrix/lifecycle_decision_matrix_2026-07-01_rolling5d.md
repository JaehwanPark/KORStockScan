# Lifecycle Decision Matrix - 2026-07-01

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-01_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `20935`
- source_rows_total: `42105`
- retained_rows: `20935`
- dropped_rows_by_source: `{}`
- joined_rows: `11036`
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
- lifecycle_flow_bucket_count: `158`
- lifecycle_flow_complete_count: `40`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.002`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1342 | 145 | 1.0816 | 0.6985 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 326 | 88 | -0.377 | 0.8045 | `pass` | `NO_CHANGE` | False |
| `holding` | 214 | 88 | -0.4882 | 0.9008 | `pass` | `EXIT` | False |
| `scale_in` | 10624 | 10532 | -0.7472 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 8429 | 183 | -0.7295 | 0.1518 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 158, 'complete_flow_count': 40, 'incomplete_flow_count': 19521, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8934 | 8871 | -0.9873 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1576 | 1547 | 0.63 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b3a435d983` | 93 | 93 | -1.0309 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_wait:2f82bccefe` | 66 | 66 | 1.2913 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 33 | 33 | 1.3951 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 12 | 12 | 2.3684 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8f11eac72c` | 12 | 12 | -0.0563 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:2e5e6a8919` | 3 | 3 | -1.3825 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:b44eaf824c` | 3 | 3 | -0.9967 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8c4b62cc28` | 2 | 2 | -0.695 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8aa313d5fb` | 2 | 2 | -0.66 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:c7dbb66715` | 1 | 1 | -1.54 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ce511c4ca6` | 1 | 1 | -1.4427 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b17339bebb` | 1 | 1 | 2.9613 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:65ec45aaab` | 1 | 1 | -1.6151 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:a5aac23c60` | 1 | 1 | -0.115 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b98d884054` | 1 | 1 | -0.43 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:b620fd9627` | 1 | 1 | -1.396 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:993b58ea5f` | 1 | 1 | 1.1 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5c17a4eb7d` | 1 | 1 | -0.1886 | `hold_no_edge` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 323, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `liquidity_high` | 939 | 140 | 1.1485 | 2.0082 | 0.5857 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 191 | 115 | 1.3943 | 2.4033 | 0.5826 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1308 | 111 | 1.4386 | 2.4823 | 0.5766 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 731 | 99 | 0.7942 | 1.353 | 0.6061 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 147 | 39 | 2.3322 | 4.0137 | 0.6923 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 39 | 39 | 2.3322 | 4.0137 | 0.6923 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strong_strength_momentum` | 67 | 35 | 1.7018 | 3.0947 | 0.6571 | `hold_no_edge` |
| `time_bucket` | `time_1200_1400` | 163 | 31 | 1.6072 | 4.135 | 0.742 | `candidate_recovery_or_relax` |
| `chosen_action` | `NO_BUY_AI` | 928 | 26 | 0.0471 | 0.2234 | 0.6154 | `hold_no_edge` |
| `score_band` | `score_70p` | 187 | 26 | 1.1931 | 2.2092 | 0.6154 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 21 | 21 | -0.4423 | 2.1319 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 120 | 20 | 2.5318 | 4.8552 | 0.65 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 274 | 19 | -0.3845 | 0.479 | 0.7369 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 18 | 18 | 0.7718 | 1.2423 | 0.5 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 14 | 14 | 0.5709 | 0.7091 | 0.4286 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 141 | 14 | 1.2789 | 1.694 | 0.7143 | `hold_sample` |
| `overbought_bucket` | `overbought_watch` | 189 | 13 | 1.2619 | 0.5869 | 0.3846 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 192 | 13 | 0.3399 | 1.5822 | 0.7693 | `hold_sample` |
| `score_band` | `score_63_65` | 46 | 11 | 2.9302 | 4.8781 | 0.8182 | `hold_sample` |
| `score_band` | `score_66_69` | 38 | 11 | 1.6079 | 4.4386 | 0.8182 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 10 | 10 | 0.9273 | 1.1505 | 0.8 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 113, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 223 | 88 | -0.377 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 202 | 88 | -0.377 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 202 | 88 | -0.377 | `keep_collecting` |
| `latency_state` | `simulated` | 202 | 88 | -0.377 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 223 | 88 | -0.377 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 202 | 88 | -0.377 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 179 | 77 | -0.4188 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 293 | 72 | -0.4882 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 159 | 70 | -0.2731 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 159 | 70 | -0.2731 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 144 | 61 | -0.3498 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 152 | 61 | -0.3498 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 144 | 61 | -0.3498 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 134 | 54 | -0.5223 | `keep_collecting` |
| `would_limit_fill` | `true` | 74 | 35 | -0.2084 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 70 | 34 | -0.1462 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 58 | 27 | -0.4384 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 194 | 26 | -0.5401 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 45 | 24 | -0.3727 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 42 | 20 | 0.0517 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 45 | 18 | -0.7811 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 43 | 18 | -0.7811 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 55 | 18 | -0.7949 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 43 | 18 | -0.7811 | `keep_collecting` |
| `price_resolution_bucket` | `scalp_sim_initial_limit` | 20 | 15 | 0.5721 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 32 | 15 | -0.5553 | `source_quality_workorder` |
| `revalidation_state` | `warning_stale_context_or_quote` | 30 | 15 | 0.3634 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 38 | 12 | -1.7015 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 15 | 9 | 0.2472 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 20 | 8 | -0.3841 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 15 | 8 | 0.033 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 11 | 7 | 0.8833 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 19 | 6 | -2.0645 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 6 | 6 | 0.0094 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 3 | 3 | 0.715 | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 36, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 202 | 88 | -0.4882 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 202 | 88 | -0.4882 | `hold_no_edge` |
| `holding_action` | `WAIT` | 191 | 80 | -0.5935 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 40 | 34 | -2.0226 | `candidate_tighten_or_exclude` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 32 | 32 | -2.0394 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos150_pos300` | 19 | 19 | 1.0683 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 18 | 16 | 0.0594 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 16 | 16 | 0.9681 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 14 | 14 | -0.0136 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_neg070_neg010` | 15 | 11 | -0.2273 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 11 | 11 | -0.2273 | `hold_no_edge` |
| `holding_action` | `holding_action_not_applicable_at_start` | 9 | 7 | 0.9001 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 0.9718 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 6 | 6 | 0.7891 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 3 | 3 | 1.6029 | `candidate_recovery_or_relax` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.57 | `hold_sample` |
| `holding_action` | `BUY` | 2 | 1 | -1.79 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.79 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.25 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.7162 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_pos150_pos300_plus|held=held_not_applicable_at_start` | 1 | 1 | 2.0684 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 7 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 114 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 111 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_lt_neg070|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_pos080_pos150|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 53, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 114 | 114 | -0.8978 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 114 | 114 | -0.8978 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 114 | 114 | -0.8978 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 97 | 97 | -1.4594 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 71 | 71 | -1.2767 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 57 | 57 | -0.4284 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 46 | 46 | -0.4428 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 36 | 36 | -0.5133 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 28 | 28 | 0.702 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 23 | 23 | -0.9531 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 18 | 18 | -0.254 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 16 | 16 | 0.1297 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 15 | 15 | 0.3919 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos150_pos300` | 14 | 14 | 0.8939 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_soft_stop_pct` | 14 | 14 | -1.6902 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_unknown` | 8258 | 12 | -0.5594 | `source_quality_workorder` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.5594 | `hold_no_edge` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.5594 | `hold_no_edge` |
| `exit_rule` | `daily_limit_up_immediate_exit` | 8 | 8 | 0.0065 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300_plus` | 7 | 7 | 1.3699 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_hard_stop_pct` | 6 | 6 | -3.2854 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_lt_neg070` | 6 | 6 | -1.2562 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=daily_limit_up_immediate_exit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 6 | 6 | -0.1683 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 6 | 6 | -0.3611 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -1.2976 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 5 | 5 | -1.5344 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300` | 5 | 5 | 0.1853 | `candidate_recovery_or_relax` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos150_pos300` | 5 | 5 | 1.8062 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 4 | 4 | 0.115 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 4 | 4 | -2.3758 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos150_pos300_plus` | 4 | 4 | 0.392 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 3 | 3 | 0.07 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_pos080_pos150` | 3 | 3 | 1.0633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -3.9978 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -2.5731 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 3 | 3 | 1.1036 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_pos080_pos150` | 2 | 2 | 0.8512 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 1.596 | `hold_sample` |
| `exit_rule` | `scalp_ai_momentum_decay` | 1 | 1 | -0.754 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 315, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_source` | `score_field_backfilled` | 10528 | 10528 | None | -0.8215 | 0.1432 | `hold_sample` |
| `arm` | `AVG_DOWN` | 9035 | 8972 | None | -1.0628 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8923 | 8860 | None | -1.0338 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_70p` | 6134 | 6134 | None | -0.8142 | 0.1638 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2313 | 2313 | None | -1.0278 | 0.0826 | `hold_sample` |
| `ai_score_band` | `score_66_69` | 2263 | 2263 | None | -0.8391 | 0.1074 | `hold_sample` |
| `arm` | `PYRAMID` | 1589 | 1560 | None | 0.57 | 0.9685 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1589 | 1560 | None | 0.57 | 0.9685 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 1454 | 1454 | None | 0.4869 | 0.9663 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 913 | 913 | None | -1.0165 | 0.057 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 842 | 842 | None | -0.9479 | 0.0653 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 665 | 665 | None | -0.7846 | 0.1248 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 624 | 624 | None | -0.6988 | 0.1939 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 443 | 443 | None | -0.8561 | 0.1422 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.54)` | 356 | 356 | None | -0.54 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.23)` | 277 | 277 | None | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.68)` | 197 | 197 | None | -0.68 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.46)` | 192 | 192 | None | -1.46 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.68)` | 191 | 191 | None | -1.68 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 186 | 186 | None | -0.6856 | 0.1613 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 24 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 12 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 24 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `stage` | `exit` | 12 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 24 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 12 | 12 | -0.5594 | -0.7458 | 0.1667 | `hold_sample` |
| `price_source` | `holding_price_samples_last` | 22 | 11 | -0.5945 | -0.7927 | 0.1818 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 20 | 10 | -0.8415 | -1.122 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 14 | 7 | -0.0739 | -0.0986 | 0.2857 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 6 | 6 | -1.2562 | -1.675 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 12 | 6 | -1.2562 | -1.675 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 8 | 4 | -1.3519 | -1.8025 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.2193 | -0.2925 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos080_pos150` | 2 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `peak_profit_band` | `peak_pos080_pos150` | 4 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 2 | 0.8512 | 1.135 | 1.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.7875 | -1.05 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 12 | 0 | None | None | None | `hold_sample` |

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
