# Lifecycle Decision Matrix - 2026-07-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-29_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2550`
- source_rows_total: `6719`
- retained_rows: `2550`
- dropped_rows_by_source: `{}`
- joined_rows: `728`
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
- lifecycle_flow_bucket_count: `91`
- lifecycle_flow_complete_count: `22`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0167`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1387 | 9 | -0.0357 | 0.0122 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 361 | 13 | 0.1412 | 0.0468 | `pass` | `NO_CHANGE` | False |
| `holding` | 47 | 13 | -0.6252 | 0.2331 | `pass` | `EXIT` | False |
| `scale_in` | 647 | 646 | -0.4981 | 0.9904 | `pass` | `NO_CHANGE` | False |
| `exit` | 108 | 47 | -0.7101 | 0.5451 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 91, 'complete_flow_count': 22, 'incomplete_flow_count': 1299, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 555 | 554 | -0.6695 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 92 | 92 | 0.5339 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 9 | 9 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 7 | 7 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 1 | 1 | -0.35 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:5f3f5e5611` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:a6f85bdcc6` | 1 | 1 | -0.422 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3de51bc35d` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:a8a00e350f` | 1 | 1 | -1.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b7151ca7a` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c6b7b772fb` | 1 | 1 | -1.63 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d0ed1aa56b` | 1 | 1 | 2.3727 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:e48ea83ea5` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 182, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | 0.169 | -1.4643 | 0.0 | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 229 | 6 | 0.3563 | -1.419 | 0.0 | `hold_sample` |
| `score_band` | `score_lt60` | 1205 | 6 | -0.1366 | -1.1884 | 0.1666 | `source_quality_workorder` |
| `chosen_action` | `NO_BUY_AI` | 451 | 5 | 0.5119 | -1.482 | 0.0 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 258 | 5 | 0.5119 | -1.482 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1204 | 5 | 0.5119 | -1.482 | 0.0 | `source_quality_workorder` |
| `time_bucket` | `time_0900_1000` | 285 | 5 | -0.0306 | -1.0748 | 0.2 | `source_quality_workorder` |
| `stale_bucket` | `stale_high` | 173 | 4 | 0.5305 | -1.4875 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 433 | 4 | -0.0423 | -1.4525 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 49 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 1074 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 1046 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 10 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 10 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `stale_bucket` | `stale_not_available` | 714 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 161 | 3 | 0.4318 | -1.4867 | 0.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 863 | 2 | 0.6321 | -1.475 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 42 | 2 | 0.6038 | -1.485 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 8 | 2 | -0.6883 | -1.42 | 0.0 | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 748 | 1 | -0.422 | -1.1039 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 121, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 277 | 13 | 0.1412 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 39 | 13 | 0.1412 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 330 | 13 | 0.1412 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 39 | 13 | 0.1412 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 39 | 13 | 0.1412 | `keep_collecting` |
| `latency_state` | `simulated` | 39 | 13 | 0.1412 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 277 | 13 | 0.1412 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 39 | 13 | 0.1412 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 31 | 9 | 0.0597 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 31 | 9 | 0.0597 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 261 | 9 | 0.0597 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 31 | 9 | 0.0597 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 31 | 9 | 0.0597 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 29 | 7 | -0.0608 | `keep_collecting` |
| `would_limit_fill` | `false` | 342 | 6 | -0.2015 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 10 | 6 | 0.3769 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 8 | 4 | 0.3246 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 8 | 4 | 0.3246 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 8 | 4 | 0.3246 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 8 | 4 | 0.3246 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 8 | 4 | 0.3246 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 3 | -0.8198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 3 | 0.4169 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 11 | 3 | 0.582 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 6 | 2 | 0.6167 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 2 | 0.6543 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 61 | 1 | 4.1198 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 27 | 1 | -4.055 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 1 | 0.4374 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1637 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 1.0697 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -4.055 | `source_quality_workorder` |
| `latency_state` | `caution` | 44 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 44 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 22, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 39 | 13 | -0.6252 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 39 | 13 | -0.6252 | `hold_no_edge` |
| `holding_action` | `WAIT` | 38 | 12 | -0.5415 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 10 | 10 | -0.8623 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 9 | 9 | -0.7771 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | 0.9452 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 2 | 2 | 0.9452 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 8 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 8 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 2 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 5 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 37, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 30 | 30 | -1.003 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 27 | 27 | -0.9034 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 27 | 27 | -0.9034 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 27 | 27 | -0.9034 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 21 | 21 | -1.0471 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 13 | 13 | -0.3161 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 12 | 12 | -0.6336 | `hold_no_edge` |
| `exit_outcome` | `COMPLETED` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 8 | 8 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 7 | 7 | -0.6577 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.2336 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.546 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.4773 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `GOOD_EXIT` | 3 | 3 | -1.0955 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 3 | 3 | -0.9716 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 3 | 3 | 0.7402 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 3 | 3 | 0.1652 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -1.7473 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 2 | 2 | -0.6426 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.8651 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.6295 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 61 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 61 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 44 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 44 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 17 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 17 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 44 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 17 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 170, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 647 | 646 | None | -0.5833 | 0.1424 | `hold_sample` |
| `qty_reason` | `qty_none` | 646 | 646 | None | -0.5833 | 0.1424 | `hold_sample` |
| `time_bucket` | `time_unknown` | 647 | 646 | None | -0.5833 | 0.1424 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 642 | 642 | None | -0.583 | 0.1417 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 604 | 603 | None | -0.581 | 0.1526 | `hold_sample` |
| `arm` | `AVG_DOWN` | 555 | 554 | None | -0.7629 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 552 | 551 | None | -0.7488 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 467 | 467 | None | -0.7901 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 295 | 295 | None | -0.6317 | 0.0847 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 275 | 275 | None | -0.4336 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 267 | 267 | None | -1.1343 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 212 | 212 | None | -0.5539 | 0.2217 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 205 | 205 | None | -0.609 | 0.1268 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 160 | 160 | None | -0.554 | 0.1625 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 134 | 134 | None | -0.6075 | 0.1716 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 127 | 127 | None | -0.5611 | 0.126 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 119 | 119 | None | -0.0283 | 0.6471 | `hold_sample` |
| `arm` | `PYRAMID` | 92 | 92 | None | 0.4987 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 92 | 92 | None | 0.4987 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 89 | 89 | None | 0.2606 | 0.8652 | `hold_sample` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- none

## Overnight Bucket Attribution

- decision_authority: `aggregated_overnight_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 17, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overnight_action` | `SELL_TODAY` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 16 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 8 | 8 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 10 | 5 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 8 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 8 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 8 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 8 | 0 | None | None | None | `hold_sample` |

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
