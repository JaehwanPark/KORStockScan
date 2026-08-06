# Lifecycle Decision Matrix - 2026-08-05

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-05_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6191`
- source_rows_total: `11937`
- retained_rows: `6191`
- dropped_rows_by_source: `{}`
- joined_rows: `1872`
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
- lifecycle_flow_bucket_count: `101`
- lifecycle_flow_complete_count: `25`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0069`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `['scale_in_counterfactual_instrumentation_gap']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 3778 | 115 | 3.1695 | 0.2605 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 240 | 19 | -0.1993 | 0.1143 | `pass` | `NO_CHANGE` | False |
| `holding` | 31 | 19 | -0.5312 | 0.2458 | `pass` | `EXIT` | False |
| `scale_in` | 1682 | 1675 | -0.6085 | 0.9976 | `pass` | `NO_CHANGE` | False |
| `exit` | 460 | 44 | -0.6416 | 0.1797 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 25, 'incomplete_flow_count': 3592, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1474 | 1468 | -0.754 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 208 | 207 | 0.4231 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 91 | 91 | 3.8218 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 5 | 5 | 3.2465 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 4 | 4 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 3 | 3 | -0.93 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 3 | 3 | -0.6933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 3 | 3 | -0.4433 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:5159f83a5b` | 1 | 1 | -1.1229 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:38511f6f01` | 1 | 1 | -0.6279 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:eb99aaba9b` | 1 | 1 | -0.47 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b436f64c2` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 363, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 832 | 105 | 3.3473 | 5.3051 | 0.6381 | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 1618 | 99 | 3.6898 | 5.9309 | 0.6969 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 836 | 97 | 3.794 | 6.0876 | 0.6907 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 3760 | 97 | 3.794 | 6.0876 | 0.6907 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 97 | 97 | 3.794 | 6.0876 | 0.6907 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 1081 | 64 | 3.3542 | 5.2066 | 0.6719 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 165 | 34 | 4.4636 | 7.588 | 0.5882 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 34 | 34 | 3.1844 | 4.6345 | 0.7059 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 20 | 20 | 1.4614 | 2.2098 | 0.65 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 495 | 20 | 2.485 | 3.5671 | 0.5 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_normal` | 697 | 17 | 0.6873 | 0.816 | 0.5882 | `hold_sample` |
| `strength_bucket` | `weak_strength_momentum` | 766 | 17 | 6.2804 | 10.5422 | 0.7647 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 372 | 15 | -0.3195 | -1.2547 | 0.2 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 1749 | 15 | -0.3195 | -1.2547 | 0.2 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1274 | 15 | -0.3195 | -1.2547 | 0.2 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 355 | 15 | -0.3195 | -1.2547 | 0.2 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 216 | 14 | -0.4239 | -1.23 | 0.2143 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 743 | 14 | -0.4239 | -1.23 | 0.2143 | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 731 | 13 | 3.7709 | 6.3765 | 0.6154 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 327 | 12 | 6.6422 | 11.7907 | 0.8333 | `hold_sample` |

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
| `actual_order_submitted` | `false` | 182 | 19 | -0.1993 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 24 | 19 | -0.1993 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 238 | 19 | -0.1993 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 27 | 19 | -0.1993 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 27 | 19 | -0.1993 | `keep_collecting` |
| `latency_state` | `simulated` | 27 | 19 | -0.1993 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 182 | 19 | -0.1993 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 27 | 19 | -0.1993 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 21 | 15 | -0.3195 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 18 | 13 | -0.0194 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 18 | 13 | -0.0194 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 172 | 13 | -0.0194 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 18 | 13 | -0.0194 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 18 | 13 | -0.0194 | `keep_collecting` |
| `would_limit_fill` | `false` | 226 | 9 | -0.2899 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 11 | 8 | -0.3696 | `source_quality_workorder` |
| `liquidity_bucket` | `below_min_liquidity` | 9 | 6 | -0.5893 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 9 | 6 | -0.5893 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 9 | 6 | -0.5893 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 9 | 6 | -0.5893 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 9 | 6 | -0.5893 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 24 | 5 | -0.1061 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 6 | 4 | 0.2512 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 4 | 4 | -0.0678 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 5 | 4 | 0.5893 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 2 | 0.7201 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.4585 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 25 | 1 | -3.0049 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 2 | 1 | 0.3474 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | -3.0049 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 3 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 46 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 46 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 158 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 23, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 27 | 19 | -0.5312 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 27 | 19 | -0.5312 | `candidate_tighten_or_exclude` |
| `holding_action` | `WAIT` | 25 | 18 | -0.5722 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 10 | 10 | -1.1257 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 10 | 10 | -1.1257 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | -0.0634 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 5 | 5 | -0.1174 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8287 | `hold_sample` |
| `holding_action` | `BUY` | 1 | 1 | 0.2066 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 5 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=BUY|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 0.2066 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 4 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 8 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 4 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 7 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 3 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 40, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 22 | 22 | -1.1035 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 21 | 21 | -0.831 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 21 | 21 | -0.831 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 21 | 21 | -0.831 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 19 | 19 | -0.5312 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.4279 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 12 | 12 | -1.085 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 9 | 9 | -0.469 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 9 | 9 | 0.1294 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 8 | 8 | -0.6727 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 8 | 8 | -0.595 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 7 | 7 | -0.0072 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 6 | 6 | -0.1898 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 5 | 5 | -0.4847 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -1.1832 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 4 | 4 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -2.9375 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.7747 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 2 | 2 | -0.2107 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -2.5775 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 416 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 416 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 362 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 362 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 54 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 54 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 362 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 54 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 189, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1681 | 1675 | None | -0.6747 | 0.1003 | `hold_sample` |
| `qty_reason` | `qty_none` | 1676 | 1675 | None | -0.6747 | 0.1003 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1682 | 1675 | None | -0.6747 | 0.1003 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1660 | 1659 | None | -0.6907 | 0.0916 | `hold_sample` |
| `arm` | `AVG_DOWN` | 1474 | 1468 | None | -0.8255 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 1468 | 1462 | None | -0.8155 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 938 | 931 | None | -0.5662 | 0.1804 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 782 | 782 | None | -0.5994 | 0.0678 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 769 | 769 | None | -0.4406 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 751 | 744 | None | -0.8103 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 664 | 664 | None | -0.8035 | 0.0994 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 653 | 653 | None | -1.3328 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 612 | 612 | None | -0.4961 | 0.1487 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 591 | 591 | None | -0.8218 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 339 | 339 | None | -0.6606 | 0.1416 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 303 | 303 | None | -0.2314 | 0.4389 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 296 | 296 | None | -0.8365 | 0.1892 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 260 | 260 | None | -0.8574 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 230 | 230 | None | 0.2456 | 0.6304 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 217 | 217 | None | -0.7537 | 0.0323 | `hold_sample` |

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
| `held_bucket` | `held_600_1800s_plus` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
