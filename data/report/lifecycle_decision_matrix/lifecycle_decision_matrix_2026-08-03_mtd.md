# Lifecycle Decision Matrix - 2026-08-03

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-08-03_mtd`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1535`
- source_rows_total: `2774`
- retained_rows: `1535`
- dropped_rows_by_source: `{}`
- joined_rows: `131`
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
- lifecycle_flow_bucket_count: `46`
- lifecycle_flow_complete_count: `3`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0041`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1238 | 65 | 3.3648 | 0.3413 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 69 | 2 | 1.2247 | 0.0058 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 3 | 2 | 0.4752 | 0.1333 | `pass` | `HOLD` | False |
| `scale_in` | 58 | 58 | -0.8649 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 167 | 4 | -0.2299 | 0.0096 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 46, 'complete_flow_count': 3, 'incomplete_flow_count': 728, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:0b05a5c5af` | 58 | 58 | 3.4417 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 53 | 53 | -1.0143 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5 | 5 | 0.718 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:7535817223` | 4 | 4 | 3.1589 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:99013dc4f3` | 1 | 1 | 1.2012 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:d0233209ef` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_wa:2a245e5d4f` | 1 | 1 | 4.0086 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -1.04 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:db8bbc6230` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:c18e731ca8` | 13 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:9a372901ee` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_bl:cf6cca51c3` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:b90a5c668a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:6d88d558c7` | 7 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:1c4ab1bc7c` | 18 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 109 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:0370c0d68d` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_bl:98023dd644` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_sc:ccaec8e263` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 200, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `WAIT_REQUOTE` | 389 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `exit_rule` | `exit_unknown` | 1236 | 63 | 3.4327 | 5.2779 | 0.746 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 390 | 63 | 3.3899 | 5.2021 | 0.746 | `candidate_recovery_or_relax` |
| `source_stage` | `wait6579_ev_cohort` | 63 | 63 | 3.4327 | 5.2779 | 0.746 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 349 | 61 | 3.3783 | 5.1335 | 0.7377 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_watch` | 350 | 42 | 2.5652 | 3.623 | 0.6905 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_1000_1200` | 24 | 24 | 2.7518 | 3.8641 | 0.6667 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_watch|time=time_0900_1000` | 15 | 15 | 2.187 | 3.0597 | 0.7333 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_ok` | 81 | 11 | 6.2502 | 11.1017 | 0.8182 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_ok|time=time_1000_1200` | 9 | 9 | 7.6585 | 13.6406 | 0.8889 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 104 | 6 | 1.636 | 1.7295 | 0.8333 | `hold_sample` |
| `overbought_bucket` | `overbought_chase_risk` | 44 | 5 | 6.2529 | 9.7913 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 5 | 5 | 1.4503 | 1.4482 | 0.8 | `hold_sample` |
| `score_band` | `score_66_69` | 32 | 4 | 3.1589 | 4.7184 | 0.75 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_high|overbought=overbought_chase_risk|time=time_1000_1200` | 3 | 3 | 7.5937 | 12.2302 | 1.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 519 | 1 | 1.3075 | 1.11 | 1.0 | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 143 | 1 | 1.1418 | -1.6 | 0.0 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_mid` | 43 | 1 | 4.0086 | 5.8844 | 1.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 654 | 1 | 1.1418 | -1.6 | 0.0 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 516 | 1 | 1.1418 | -1.6 | 0.0 | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 84, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 55 | 2 | 1.2247 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 3 | 2 | 1.2247 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 69 | 2 | 1.2247 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 3 | 2 | 1.2247 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 3 | 2 | 1.2247 | `keep_collecting` |
| `latency_state` | `simulated` | 3 | 2 | 1.2247 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 55 | 2 | 1.2247 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3 | 2 | 1.2247 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 1 | 1.1418 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1 | 1 | 1.1418 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 2 | 1 | 1.3075 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 1 | 1 | 1.1418 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 2 | 1 | 1.3075 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 2 | 1 | 1.3075 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 9 | 1 | 1.1418 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 54 | 1 | 1.3075 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 2 | 1 | 1.3075 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 1 | 1 | 1.1418 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | 1.3075 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 1.1418 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 1 | 1 | 1.3075 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 1 | 1 | 1.1418 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1 | 1 | 1.1418 | `source_quality_workorder` |
| `liquidity_guard_action` | `would_pass` | 2 | 1 | 1.3075 | `keep_collecting` |
| `latency_state` | `caution` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 53 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 14 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 14 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 67 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 52 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 1 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 66 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 66 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 14 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 9, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 3 | 2 | 0.4752 | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 3 | 2 | 0.4752 | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 2 | 0.4752 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -0.2509 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.2509 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | 1.2012 | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 20, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 3 | 3 | -0.707 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 2 | 2 | 0.4752 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 2 | 2 | -0.935 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 2 | 2 | 0.4752 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -0.935 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 1 | 1 | -0.2509 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | 1.2012 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -0.2509 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_pos080_pos150` | 1 | 1 | 1.2012 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 163 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 163 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 141 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 141 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 22 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 22 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 141 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 22 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 58 | 58 | None | -0.9517 | 0.0862 | `hold_sample` |
| `qty_reason` | `qty_none` | 58 | 58 | None | -0.9517 | 0.0862 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 58 | 58 | None | -0.9517 | 0.0862 | `hold_sample` |
| `time_bucket` | `time_unknown` | 58 | 58 | None | -0.9517 | 0.0862 | `hold_sample` |
| `arm` | `AVG_DOWN` | 53 | 53 | None | -1.1092 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 53 | 53 | None | -1.1092 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 34 | 34 | None | -1.5374 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 29 | 29 | None | -1.09 | 0.1034 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 29 | 29 | None | -1.0931 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 29 | 29 | None | -0.8103 | 0.1724 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 25 | 25 | None | -0.8272 | 0.04 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 24 | 24 | None | -1.3129 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 19 | 19 | None | -0.3432 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 18 | 18 | None | -0.9317 | 0.1111 | `hold_sample` |
| `held_bucket` | `held_lt020s` | 15 | 15 | None | -0.38 | 0.2 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_0` | 14 | 14 | None | -1.3021 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 13 | 13 | None | -1.2038 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 12 | 12 | None | -0.895 | 0.1667 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 8 | 8 | None | -0.9663 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 6 | 6 | None | -1.37 | 0.0 | `hold_sample` |

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
