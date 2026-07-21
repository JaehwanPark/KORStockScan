# Lifecycle Decision Matrix - 2026-07-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-20_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `1207`
- source_rows_total: `2764`
- retained_rows: `1207`
- dropped_rows_by_source: `{}`
- joined_rows: `583`
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
- lifecycle_flow_bucket_count: `47`
- lifecycle_flow_complete_count: `10`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0115`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 343 | 5 | 0.1591 | 0.0263 | `pass` | `NO_CHANGE` | False |
| `submit` | 95 | 9 | 0.2266 | 0.1751 | `pass` | `ALLOW_SUBMIT` | False |
| `holding` | 17 | 9 | -0.2194 | 0.3042 | `pass` | `EXIT` | False |
| `scale_in` | 542 | 540 | -0.6127 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 210 | 20 | -0.619 | 0.1435 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 47, 'complete_flow_count': 10, 'incomplete_flow_count': 863, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 465 | 463 | -0.8702 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 77 | 77 | 0.9356 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:3c997aea8d` | 2 | 2 | -0.935 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:19270f18a8` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:1f33988758` | 1 | 1 | -0.71 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:e7d176584e` | 1 | 1 | -0.67 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai:5a753e3e56` | 1 | 1 | -1.5656 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3de51bc35d` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:ecfc6ee6b1` | 1 | 1 | -0.8553 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:8858a17062` | 1 | 1 | -1.21 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:a8a00e350f` | 1 | 1 | -1.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:75c7602241` | 1 | 1 | -0.89 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c6b7b772fb` | 1 | 1 | -1.63 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d0ed1aa56b` | 1 | 1 | 2.3727 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:12b48c8f43` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:04fe106012` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:0e304b8817` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:542cd2bc91` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:b58865037e` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 110, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 117 | 5 | 0.1591 | 0.074 | 0.8 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 49 | 5 | 0.1591 | 0.074 | 0.8 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 47 | 5 | 0.1591 | 0.074 | 0.8 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 298 | 5 | 0.1591 | 0.074 | 0.8 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 47 | 5 | 0.1591 | 0.074 | 0.8 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 4 | 4 | -0.4408 | 1.16 | 1.0 | `hold_sample` |
| `stale_bucket` | `stale_high` | 54 | 4 | -0.4408 | 1.16 | 1.0 | `hold_sample` |
| `score_band` | `score_lt60` | 293 | 3 | 0.4424 | -0.6833 | 0.6667 | `source_quality_workorder` |
| `time_bucket` | `time_1000_1200` | 97 | 3 | -0.3103 | 1.25 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 2 | -0.266 | 1.21 | 1.0 | `hold_sample` |
| `score_band` | `score_60_62` | 18 | 2 | -0.266 | 1.21 | 1.0 | `hold_sample` |
| `stale_bucket` | `fresh` | 19 | 1 | 2.5584 | -4.27 | 0.0 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 1 | 1 | 2.5584 | -4.27 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 2.5584 | -4.27 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 2 | 1 | -0.399 | 1.33 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1200_1400` | 9 | 1 | -0.8321 | 0.89 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 66 | 1 | 2.5584 | -4.27 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1200_1400` | 92 | 1 | -0.8321 | 0.89 | 1.0 | `hold_sample` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 12 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 15 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 101, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 76 | 9 | 0.2266 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 89 | 9 | 0.2266 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 15 | 9 | 0.2266 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 15 | 9 | 0.2266 | `keep_collecting` |
| `latency_state` | `simulated` | 15 | 9 | 0.2266 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 76 | 9 | 0.2266 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 15 | 9 | 0.2266 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 14 | 8 | -0.0649 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 11 | 7 | -0.6627 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 6 | 5 | 0.1591 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 6 | 5 | 0.1591 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 66 | 5 | 0.1591 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 6 | 5 | 0.1591 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 6 | 5 | 0.1591 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 9 | 4 | 0.3111 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 9 | 4 | 0.3111 | `keep_collecting` |
| `would_limit_fill` | `false` | 85 | 4 | 0.3712 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 9 | 4 | 0.3111 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 9 | 4 | 0.3111 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 9 | 4 | 0.3111 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 4 | 3 | -0.3578 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_context_missing` | 4 | 2 | 3.3391 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 14 | 2 | -1.9726 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 2 | -1.9726 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | 2.5584 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 3 | 1 | 1.0697 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 11 | 1 | 4.1198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 1 | 1 | 2.5584 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 1 | 1 | -0.6896 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 3 | 1 | 1.0697 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 1 | 1 | -0.6896 | `keep_collecting` |
| `latency_state` | `caution` | 8 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 8 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 65 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 22, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 15 | 9 | -0.2194 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 15 | 9 | -0.2194 | `hold_no_edge` |
| `holding_action` | `WAIT` | 14 | 8 | -0.1399 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 3 | 3 | -1.4287 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.3152 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 3 | 3 | -0.3152 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 1.0046 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.7153 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 1.0046 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -0.8553 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos150_pos300|held=held_not_applicable_at_start` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -0.8553 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 1 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 11 | 11 | -1.2433 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 9 | 9 | -1.1178 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 9 | 9 | -1.1178 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 9 | 9 | -1.1178 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 9 | 9 | -0.2194 | `hold_no_edge` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 8 | 8 | -1.1738 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_trailing_take_profit` | 6 | 6 | 0.3853 | `candidate_recovery_or_relax` |
| `exit_outcome` | `GOOD_EXIT` | 4 | 4 | -0.3273 | `hold_no_edge` |
| `exit_outcome` | `MISSED_UPSIDE` | 3 | 3 | -0.1159 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 3 | -0.3384 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 3 | 3 | -0.3152 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 3 | 3 | -1.4287 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 3 | 3 | -0.3152 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 2 | 2 | -0.1588 | `hold_sample` |
| `exit_outcome` | `outcome_unknown` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 1.0046 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 2 | 2 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=outcome_unknown|profit=profit_neg070_neg010` | 2 | 2 | -0.1725 | `source_quality_workorder` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 2 | 2 | -1.3602 | `hold_sample` |
| `profit_band` | `profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 1 | 1 | -0.67 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.5656 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.3636 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=NEUTRAL|profit=profit_pos150_pos300` | 1 | 1 | 1.2481 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 190 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 190 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 12 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 12 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 178 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 178 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 178 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 148, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 542 | 540 | None | -0.7423 | 0.1426 | `hold_sample` |
| `qty_reason` | `qty_none` | 540 | 540 | None | -0.7423 | 0.1426 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 542 | 540 | None | -0.7423 | 0.1426 | `hold_sample` |
| `time_bucket` | `time_unknown` | 542 | 540 | None | -0.7423 | 0.1426 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 511 | 511 | None | -0.8224 | 0.1037 | `hold_sample` |
| `arm` | `AVG_DOWN` | 465 | 463 | None | -1.0208 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 463 | 461 | None | -1.012 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 391 | 391 | None | -1.0752 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 326 | 326 | None | -0.6124 | 0.184 | `hold_sample` |
| `ai_score_source` | `live` | 316 | 316 | None | -0.6449 | 0.1709 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 309 | 309 | None | -1.3309 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 176 | 176 | None | -0.9717 | 0.0625 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 146 | 146 | None | -0.4162 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 107 | 107 | None | -0.3988 | 0.3271 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 105 | 105 | None | -1.0534 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 77 | 77 | None | 0.9327 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 77 | 77 | None | 0.9327 | 1.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 62 | 62 | None | -1.1903 | 0.0645 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 43 | 43 | None | 0.2077 | 0.8139 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 41 | 41 | None | -0.3829 | 0.2927 | `hold_sample` |

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
