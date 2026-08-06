# Lifecycle Decision Matrix - 2026-08-05

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-05_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `4450`
- source_rows_total: `8371`
- retained_rows: `4450`
- dropped_rows_by_source: `{}`
- joined_rows: `1265`
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
- lifecycle_flow_bucket_count: `70`
- lifecycle_flow_complete_count: `16`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0063`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 2866 | 107 | 3.4481 | 0.2794 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 127 | 11 | 0.0602 | 0.1676 | `pass` | `NO_CHANGE` | False |
| `holding` | 16 | 11 | -0.2705 | 0.296 | `pass` | `EXIT` | False |
| `scale_in` | 1111 | 1110 | -0.5185 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 330 | 26 | -0.5948 | 0.1423 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 70, 'complete_flow_count': 16, 'incomplete_flow_count': 2534, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 992 | 992 | -0.6333 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 119 | 118 | 0.4461 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 91 | 91 | 3.8218 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 5 | 5 | 3.2465 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 3 | 3 | -0.6933 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b75bf201fa` | 2 | 2 | -0.745 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 2 | 2 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8b2aea4c29` | 1 | 1 | -0.86 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:075ce13c92` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:f36cc32176` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:db8bbc6230` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 8 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 313, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 744 | 102 | 3.458 | 5.4898 | 0.6568 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_high` | 1295 | 98 | 3.7239 | 5.9905 | 0.6939 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 590 | 97 | 3.794 | 6.0876 | 0.6907 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2856 | 97 | 3.794 | 6.0876 | 0.6907 | `source_quality_workorder` |
| `source_stage` | `wait6579_ev_cohort` | 97 | 97 | 3.794 | 6.0876 | 0.6907 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 888 | 64 | 3.3542 | 5.2066 | 0.6719 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 151 | 34 | 4.4636 | 7.588 | 0.5882 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 34 | 34 | 3.1844 | 4.6345 | 0.7059 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 20 | 20 | 1.4614 | 2.2098 | 0.65 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_normal` | 519 | 16 | 0.7086 | 0.8614 | 0.5625 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 245 | 16 | 3.1923 | 4.8189 | 0.625 | `candidate_recovery_or_relax` |
| `strength_bucket` | `weak_strength_momentum` | 480 | 16 | 6.6512 | 11.1955 | 0.75 | `candidate_recovery_or_relax` |
| `strength_bucket` | `neutral_strength_momentum` | 342 | 13 | 3.7709 | 6.3765 | 0.6154 | `hold_sample` |
| `overbought_bucket` | `overbought_ok` | 253 | 12 | 6.6422 | 11.7907 | 0.8333 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1200_1400` | 154 | 11 | 7.6102 | 13.2473 | 0.5455 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 280 | 8 | 0.0006 | -1.1475 | 0.25 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1201 | 8 | 0.0006 | -1.1475 | 0.25 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 846 | 8 | 0.0006 | -1.1475 | 0.25 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 266 | 8 | 0.0006 | -1.1475 | 0.25 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 89, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 100 | 11 | 0.0602 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 14 | 11 | 0.0602 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 127 | 11 | 0.0602 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 16 | 11 | 0.0602 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 16 | 11 | 0.0602 | `keep_collecting` |
| `latency_state` | `simulated` | 16 | 11 | 0.0602 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 100 | 11 | 0.0602 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 16 | 11 | 0.0602 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 11 | 8 | 0.0006 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 9 | 7 | 0.2658 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 9 | 7 | 0.2658 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 93 | 7 | 0.2658 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 9 | 7 | 0.2658 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 9 | 7 | 0.2658 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 7 | 4 | -0.2996 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 7 | 4 | -0.2996 | `keep_collecting` |
| `would_limit_fill` | `false` | 117 | 4 | 0.0684 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 7 | 4 | -0.2996 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 5 | 4 | 0.0684 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 7 | 4 | -0.2996 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 7 | 4 | -0.2996 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 5 | 3 | 0.2191 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 20 | 3 | 0.6021 | `keep_collecting` |
| `would_limit_fill` | `true` | 3 | 3 | 0.529 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 2 | 2 | 0.4585 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 1.033 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 5 | 1 | -3.0049 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 0.6701 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | -3.0049 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 20 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 86 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 27 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 13, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 16 | 11 | -0.2705 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 16 | 11 | -0.2705 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 16 | 11 | -0.2705 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 5 | 5 | -1.0086 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 5 | 5 | -1.0086 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 2 | 2 | 0.8287 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 31, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 15 | 15 | -0.8327 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 15 | 15 | -0.8327 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 15 | 15 | -0.8327 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 13 | 13 | -1.0187 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 11 | 11 | -0.2705 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 8 | -0.5503 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.025 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 7 | 7 | -0.6129 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | 0.3447 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 5 | 5 | -0.0807 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 4 | 4 | 0.0673 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 4 | 4 | -0.4364 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 3 | 3 | -0.3107 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -1.4206 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 2 | 2 | 0.8287 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.8137 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -3.2975 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | 0.4563 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 304 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 304 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 272 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 272 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 32 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 32 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 272 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 32 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 140, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1111 | 1110 | None | -0.569 | 0.0712 | `hold_sample` |
| `qty_reason` | `qty_none` | 1110 | 1110 | None | -0.569 | 0.0712 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1111 | 1110 | None | -0.569 | 0.0712 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1095 | 1094 | None | -0.5918 | 0.0576 | `hold_sample` |
| `arm` | `AVG_DOWN` | 992 | 992 | None | -0.6868 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 990 | 990 | None | -0.682 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 649 | 649 | None | -0.4411 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 636 | 636 | None | -0.3759 | 0.0834 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 611 | 610 | None | -0.4784 | 0.1295 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 501 | 500 | None | -0.6794 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 449 | 449 | None | -0.7224 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 427 | 427 | None | -0.483 | 0.0492 | `hold_sample` |
| `ai_score_source` | `live` | 383 | 383 | None | -0.5677 | 0.1306 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 311 | 311 | None | -1.265 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 193 | 193 | None | -0.7238 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 168 | 168 | None | -1.1171 | 0.0952 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 146 | 146 | None | -0.6224 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 146 | 146 | None | -0.5006 | 0.0 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 136 | 136 | None | -0.7547 | 0.0368 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_0` | 136 | 136 | None | -0.8676 | 0.0 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 0, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

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
