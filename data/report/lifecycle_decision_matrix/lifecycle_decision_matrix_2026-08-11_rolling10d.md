# Lifecycle Decision Matrix - 2026-08-11

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-11_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `8946`
- source_rows_total: `13100`
- retained_rows: `8946`
- dropped_rows_by_source: `{}`
- joined_rows: `2852`
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
- lifecycle_flow_bucket_count: `100`
- lifecycle_flow_complete_count: `35`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0071`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 5557 | 92 | 2.3264 | 0.2444 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 252 | 30 | -0.0832 | 0.2886 | `pass` | `NO_CHANGE` | False |
| `holding` | 37 | 30 | -0.4783 | 0.5607 | `pass` | `EXIT` | False |
| `scale_in` | 2665 | 2648 | -0.7639 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 435 | 52 | -0.5921 | 0.3591 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 100, 'complete_flow_count': 35, 'incomplete_flow_count': 4872, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 2420 | 2405 | -0.8857 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 245 | 243 | 0.4413 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 3 | 3 | -0.1136 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -1.0067 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:5ad377bcf7` | 1 | 1 | -0.4211 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:7dd76f2392` | 1 | 1 | -2.1224 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:4e1fc29475` | 1 | 1 | -0.904 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:31a116e56b` | 1 | 1 | -0.7246 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:7664e5a914` | 1 | 1 | -0.1193 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1fbcba9334` | 1 | 1 | 0.0719 | `hold_no_edge` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 366, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 959 | 83 | 2.4283 | 3.5693 | 0.6626 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 2799 | 66 | 3.2288 | 5.0047 | 0.7575 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 973 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 5528 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 1872 | 44 | 2.4469 | 3.4863 | 0.7046 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 497 | 25 | -0.1231 | -1.166 | 0.36 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 2206 | 25 | -0.1231 | -1.166 | 0.36 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1532 | 25 | -0.1231 | -1.166 | 0.36 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 452 | 25 | -0.1231 | -1.166 | 0.36 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 313 | 24 | -0.1758 | -1.1479 | 0.375 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_not_available` | 1179 | 24 | -0.1758 | -1.1479 | 0.375 | `source_quality_workorder` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 14 | 14 | -0.3248 | 0.5307 | 0.9286 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 169 | 12 | -0.387 | -1.0408 | 0.4167 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 529 | 11 | 6.2502 | 11.1017 | 0.8182 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | 0.6435 | -1.505 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 801 | 9 | 0.3283 | -1.0078 | 0.3333 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 225 | 30 | -0.0832 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 249 | 30 | -0.0832 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 36 | 30 | -0.0832 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 36 | 30 | -0.0832 | `keep_collecting` |
| `latency_state` | `simulated` | 36 | 30 | -0.0832 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 225 | 30 | -0.0832 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 36 | 30 | -0.0832 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 33 | 29 | -0.0773 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 31 | 27 | -0.1168 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 23 | 20 | 0.1917 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 22 | 20 | 0.1917 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 209 | 20 | 0.1917 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 22 | 20 | 0.1917 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 23 | 20 | 0.1917 | `keep_collecting` |
| `would_limit_fill` | `false` | 230 | 12 | -0.0197 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 13 | 12 | -0.0197 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 13 | 10 | -0.6328 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 14 | 10 | -0.6328 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 13 | 10 | -0.6328 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 13 | 10 | -0.6328 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 14 | 10 | -0.6328 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 26 | 8 | -0.4743 | `keep_collecting` |
| `would_limit_fill` | `true` | 8 | 8 | 0.5088 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 7 | 7 | -0.505 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 6 | 6 | 0.5255 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 5 | 3 | 0.2191 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 6 | 2 | -1.2667 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.4585 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 2 | -1.2667 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_5_20bps` | 1 | 1 | -0.2518 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 20 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 189 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 21, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 35 | 30 | -0.4783 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 35 | 30 | -0.4783 | `hold_sample` |
| `holding_action` | `WAIT` | 34 | 29 | -0.5026 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 15 | 15 | -1.0387 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 15 | 15 | -1.0387 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.1104 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 9 | 9 | -0.1477 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.6118 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 4 | 4 | 0.6118 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | 0.2255 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2255 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 39, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_source_stage` | `sim_post_sell_evaluation` | 31 | 31 | -0.4666 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 25 | 25 | -1.0352 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 19 | 19 | -0.8411 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 19 | 19 | -0.8411 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 19 | 19 | -0.8411 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 15 | 15 | 0.082 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 13 | 13 | -0.4555 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.481 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 10 | 10 | 0.0219 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 10 | 10 | -0.1104 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 10 | 10 | -0.4406 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 10 | 10 | -1.03 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 9 | 9 | -0.6311 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 8 | 8 | -1.0953 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 7 | 7 | -0.242 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 6 | 6 | 0.1911 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 5 | 5 | -2.2348 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 4 | 4 | 0.6118 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1533 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 3 | 3 | -0.9042 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 3 | 3 | -2.3487 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 3 | 3 | -0.7104 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 2 | 2 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -2.064 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 2 | 2 | 0.2074 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 2 | 2 | 1.0162 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_sim_overnight_sell_today|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.115 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | -0.1193 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 383 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 383 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 338 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 338 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 45 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 45 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 338 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 45 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 220, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 2665 | 2648 | None | -0.8346 | 0.077 | `hold_sample` |
| `qty_reason` | `qty_none` | 2648 | 2648 | None | -0.8346 | 0.077 | `hold_sample` |
| `time_bucket` | `time_unknown` | 2665 | 2648 | None | -0.8346 | 0.077 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 2624 | 2622 | None | -0.8506 | 0.0679 | `hold_sample` |
| `arm` | `AVG_DOWN` | 2420 | 2405 | None | -0.9609 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 2414 | 2399 | None | -0.9555 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1476 | 1476 | None | -0.7271 | 0.063 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1453 | 1436 | None | -0.7338 | 0.142 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1341 | 1341 | None | -1.3758 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 1231 | 1214 | None | -0.952 | 0.0016 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 1209 | 1209 | None | -0.8191 | 0.0612 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 1017 | 1017 | None | -1.0393 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 997 | 997 | None | -0.4648 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 718 | 718 | None | -0.7282 | 0.1518 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 504 | 504 | None | -0.957 | 0.133 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 477 | 477 | None | -1.1067 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 375 | 375 | None | -1.1293 | 0.0614 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 375 | 375 | None | -0.0806 | 0.432 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 325 | 325 | None | -0.8038 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 284 | 284 | None | 0.2562 | 0.6267 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 16, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 2 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 2 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | None | None | `hold_sample` |

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
