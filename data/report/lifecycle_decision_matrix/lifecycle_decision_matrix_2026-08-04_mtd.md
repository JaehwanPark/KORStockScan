# Lifecycle Decision Matrix - 2026-08-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-04_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3581`
- source_rows_total: `7423`
- retained_rows: `3581`
- dropped_rows_by_source: `{}`
- joined_rows: `1131`
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
- lifecycle_flow_bucket_count: `64`
- lifecycle_flow_complete_count: `12`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
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
| `entry` | 2154 | 69 | 3.1902 | 0.3216 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 123 | 7 | 0.5145 | 0.0347 | `pass` | `NO_CHANGE` | False |
| `holding` | 12 | 7 | 0.155 | 0.2365 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 1031 | 1030 | -0.4808 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 261 | 18 | -0.4719 | 0.1643 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 64, 'complete_flow_count': 12, 'incomplete_flow_count': 2122, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 923 | 923 | -0.5834 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 108 | 107 | 0.4031 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 2 | 2 | -0.76 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:397dbf1728` | 2 | 2 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 2 | 2 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:36dfb94c33` | 1 | 1 | -0.54 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:9e4edc4bd2` | 1 | 1 | -0.99 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -1.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0e6c01c6bb` | 1 | 1 | -0.6 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:db8bbc6230` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 47 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:cf6cca51c3` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f9f18a2ca7` | 9 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 277, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `score_band` | `score_63_65` | 583 | 65 | 3.1921 | 4.7988 | 0.7231 | `candidate_recovery_or_relax` |
| `chosen_action` | `WAIT_REQUOTE` | 555 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 2148 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 818 | 63 | 3.3899 | 5.2021 | 0.746 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 560 | 42 | 2.5652 | 3.623 | 0.6905 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 203 | 11 | 6.2502 | 11.1017 | 0.8182 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 301 | 6 | 1.636 | 1.7295 | 0.8333 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 229 | 5 | 0.5107 | -0.564 | 0.4 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1039 | 5 | 0.5107 | -0.564 | 0.4 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_chase_risk` | 75 | 5 | 6.2529 | 9.7913 | 1.0 | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 790 | 5 | 0.5107 | -0.564 | 0.4 | `source_quality_workorder` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 215 | 5 | 0.5107 | -0.564 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | 1.4503 | 1.4482 | 0.8 | `hold_sample` |
| `strength_bucket` | `risk_context_not_available` | 76 | 4 | 0.3529 | -0.305 | 0.5 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | 0.4488 | 0.3375 | 0.75 | `hold_sample` |
| `score_band` | `score_66_69` | 57 | 4 | 3.1589 | 4.7184 | 0.75 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 88, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 96 | 7 | 0.5145 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 10 | 7 | 0.5145 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 123 | 7 | 0.5145 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 12 | 7 | 0.5145 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 12 | 7 | 0.5145 | `keep_collecting` |
| `latency_state` | `simulated` | 12 | 7 | 0.5145 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 96 | 7 | 0.5145 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 12 | 7 | 0.5145 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 8 | 5 | 0.5107 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 6 | 4 | 0.4488 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 6 | 4 | 0.4488 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 90 | 4 | 0.4488 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 6 | 4 | 0.4488 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 6 | 4 | 0.4488 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 6 | 3 | 0.6021 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 6 | 3 | 0.6021 | `keep_collecting` |
| `would_limit_fill` | `false` | 116 | 3 | 0.1625 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 20 | 3 | 0.6021 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 6 | 3 | 0.6021 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | 0.1625 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_block` | 6 | 3 | 0.6021 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 6 | 3 | 0.6021 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_ok` | 4 | 2 | 0.524 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 2 | 1.033 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 1.3075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -0.2596 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 1 | 1 | 1.3075 | `keep_collecting` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 2 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 20 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 20 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 86 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 27 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 27 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 84 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 2 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 13, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 12 | 7 | 0.155 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 12 | 7 | 0.155 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 12 | 7 | 0.155 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -0.2633 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -0.2633 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg070_neg010|held=held_not_applicable_at_start` | 1 | 1 | -0.1128 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2012 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 26, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 11 | 11 | -0.8709 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 11 | 11 | -0.8709 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 11 | 11 | -0.8709 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 8 | 8 | -0.8696 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 7 | 7 | 0.155 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 6 | -0.5438 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 6 | 6 | -1.0717 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 5 | 5 | 0.3223 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.63 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 4 | 4 | 0.1026 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | 0.2249 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg010_pos080` | 3 | 3 | 0.1744 | `hold_no_edge` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.2633 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -0.2633 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_neg070_neg010` | 1 | 1 | -0.1128 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 243 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 243 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 219 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 219 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 24 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 24 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 219 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 24 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 122, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 1031 | 1030 | None | -0.5269 | 0.066 | `hold_sample` |
| `qty_reason` | `qty_none` | 1030 | 1030 | None | -0.5269 | 0.066 | `hold_sample` |
| `time_bucket` | `time_unknown` | 1031 | 1030 | None | -0.5269 | 0.066 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 1021 | 1020 | None | -0.5406 | 0.0569 | `hold_sample` |
| `arm` | `AVG_DOWN` | 923 | 923 | None | -0.6317 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 921 | 921 | None | -0.6265 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 636 | 636 | None | -0.3759 | 0.0834 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 632 | 632 | None | -0.4394 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 563 | 562 | None | -0.4433 | 0.121 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 469 | 468 | None | -0.6271 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 427 | 427 | None | -0.483 | 0.0492 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 412 | 412 | None | -0.6611 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 360 | 360 | None | -0.5187 | 0.1111 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 259 | 259 | None | -1.1729 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 182 | 182 | None | -0.6755 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 146 | 146 | None | -0.6224 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_2` | 146 | 146 | None | -0.5006 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 125 | 125 | None | -1.0434 | 0.048 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 122 | 122 | None | 0.1912 | 0.418 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 119 | 119 | None | 0.0141 | 0.3277 | `hold_sample` |

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
