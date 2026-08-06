# Lifecycle Decision Matrix - 2026-08-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-06_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7353`
- source_rows_total: `13134`
- retained_rows: `7353`
- dropped_rows_by_source: `{}`
- joined_rows: `2124`
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
- lifecycle_flow_bucket_count: `102`
- lifecycle_flow_complete_count: `27`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0066`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `['scale_in_counterfactual_instrumentation_gap']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 4575 | 83 | 2.5581 | 0.2683 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 280 | 21 | -0.2 | 0.1041 | `pass` | `NO_CHANGE` | False |
| `holding` | 33 | 21 | -0.5628 | 0.2351 | `pass` | `EXIT` | False |
| `scale_in` | 1959 | 1951 | -0.615 | 0.9987 | `pass` | `NO_CHANGE` | False |
| `exit` | 506 | 48 | -0.6531 | 0.1682 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 102, 'complete_flow_count': 27, 'incomplete_flow_count': 4081, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1731 | 1724 | -0.7511 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 228 | 227 | 0.4183 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 4 | 4 | -0.6925 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 3 | 3 | -0.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -0.4433 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 1 | 1 | -1.1229 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1729d68718` | 1 | 1 | -0.7 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:38511f6f01` | 1 | 1 | -0.6279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb99aaba9b` | 1 | 1 | -0.47 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 363, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 881 | 74 | 2.7417 | 4.0671 | 0.6622 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1984 | 65 | 3.2849 | 5.0642 | 0.7538 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 1003 | 63 | 3.4327 | 5.2779 | 0.746 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 4555 | 63 | 3.4327 | 5.2779 | 0.746 | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 1331 | 42 | 2.5652 | 3.623 | 0.6905 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 430 | 17 | -0.3061 | -1.2853 | 0.2353 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 2111 | 17 | -0.3061 | -1.2853 | 0.2353 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 1543 | 17 | -0.3061 | -1.2853 | 0.2353 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 392 | 17 | -0.3061 | -1.2853 | 0.2353 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 253 | 16 | -0.3966 | -1.2656 | 0.25 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 1008 | 16 | -0.3966 | -1.2656 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 374 | 11 | 6.2502 | 11.1017 | 0.8182 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | -0.0341 | 0.3456 | 0.7778 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 908 | 8 | 1.2216 | 1.4771 | 0.875 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | 0.1431 | -1.4613 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 135 | 8 | -0.3167 | -1.3513 | 0.25 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 104, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 224 | 21 | -0.2 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 26 | 21 | -0.2 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 277 | 21 | -0.2 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 29 | 21 | -0.2 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 29 | 21 | -0.2 | `keep_collecting` |
| `latency_state` | `simulated` | 29 | 21 | -0.2 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 224 | 21 | -0.2 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 29 | 21 | -0.2 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 23 | 17 | -0.3061 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 19 | 14 | 0.0016 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 19 | 14 | 0.0016 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 212 | 14 | 0.0016 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 19 | 14 | 0.0016 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 19 | 14 | 0.0016 | `keep_collecting` |
| `would_limit_fill` | `false` | 265 | 10 | -0.2335 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 12 | 9 | -0.298 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 10 | 7 | -0.6031 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 10 | 7 | -0.6031 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 10 | 7 | -0.6031 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 10 | 7 | -0.6031 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 10 | 7 | -0.6031 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 25 | 6 | -0.2028 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 5 | 5 | -0.1914 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 6 | 4 | 0.2512 | `keep_collecting` |
| `would_limit_fill` | `true` | 5 | 4 | 0.5893 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 2 | 0.7201 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.4585 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 23 | 1 | -3.0049 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 1 | 0.3474 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | -3.0049 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 44 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 44 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 197 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 29 | 21 | -0.5628 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 29 | 21 | -0.5628 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 27 | 20 | -0.6013 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 11 | 11 | -1.1991 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 11 | 11 | -1.1991 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.0247 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 6 | 6 | -0.0633 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8287 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | 0.2066 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 5 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 41, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 23 | 23 | -0.8191 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 23 | 23 | -1.1396 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 23 | 23 | -0.8191 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 23 | 23 | -0.8191 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 21 | 21 | -0.5628 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 15 | 15 | -0.4635 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 12 | 12 | -1.085 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 10 | 10 | 0.1372 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 10 | 10 | -0.615 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 9 | 9 | -0.469 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 8 | 8 | -0.3581 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 8 | 8 | 0.0196 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | -0.6727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.4847 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -1.1832 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 4 | 4 | 0.1827 | `hold_no_edge` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -2.6027 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7747 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.2107 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.5775 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.933 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 458 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 458 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 399 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 399 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 59 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 59 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 399 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 201, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1958 | 1951 | None | -0.6852 | 0.0964 | `hold_sample` |
| `qty_reason` | `qty_none` | 1952 | 1951 | None | -0.6852 | 0.0964 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1959 | 1951 | None | -0.6852 | 0.0964 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1928 | 1927 | None | -0.704 | 0.0851 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1731 | 1724 | None | -0.8267 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1723 | 1716 | None | -0.8156 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 1086 | 1078 | None | -0.5805 | 0.1744 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 939 | 939 | None | -0.5881 | 0.0756 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 905 | 905 | None | -0.4537 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 881 | 873 | None | -0.8145 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 768 | 768 | None | -1.3175 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 746 | 746 | None | -0.7654 | 0.1113 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 728 | 728 | None | -0.5378 | 0.1291 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 626 | 626 | None | -0.8488 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 415 | 415 | None | -0.2966 | 0.3687 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 400 | 400 | None | -0.71 | 0.125 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 335 | 335 | None | -0.8942 | 0.1672 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 287 | 287 | None | -0.8715 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 255 | 255 | None | 0.2468 | 0.647 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 233 | 233 | None | -0.741 | 0.0301 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 4 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 4 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | None | None | `hold_sample` |

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
