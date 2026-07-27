# Lifecycle Decision Matrix - 2026-07-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-27_rolling10d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2271`
- source_rows_total: `6045`
- retained_rows: `2271`
- dropped_rows_by_source: `{}`
- joined_rows: `628`
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
- lifecycle_flow_bucket_count: `79`
- lifecycle_flow_complete_count: `19`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0166`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1260 | 6 | 0.3563 | 0.0124 | `pass` | `NO_CHANGE` | False |
| `submit` | 316 | 10 | 0.4295 | 0.0473 | `pass` | `NO_CHANGE` | False |
| `holding` | 42 | 10 | -0.55 | 0.2355 | `pass` | `NO_CHANGE` | False |
| `scale_in` | 563 | 563 | -0.5512 | 0.9934 | `pass` | `NO_CHANGE` | False |
| `exit` | 90 | 39 | -0.7223 | 0.6026 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 79, 'complete_flow_count': 19, 'incomplete_flow_count': 1129, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 513 | 513 | -0.6665 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 50 | 50 | 0.6313 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 9 | 9 | -0.84 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 5 | 5 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:ddd55828ec` | 1 | 1 | -0.55 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:d65aac5eca` | 1 | 1 | -0.35 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:f58154b780` | 1 | 1 | -1.11 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai:5f3f5e5611` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_wa:a6f85bdcc6` | 1 | 1 | -0.422 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:3de51bc35d` | 1 | 1 | -1.29 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:a8a00e350f` | 1 | 1 | -1.79 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a5ddbd8b87` | 1 | 1 | -0.5 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:a1f0075e93` | 1 | 1 | -1.02 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:0b7151ca7a` | 1 | 1 | -0.83 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:c6b7b772fb` | 1 | 1 | -1.63 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:d0ed1aa56b` | 1 | 1 | 2.3727 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:e48ea83ea5` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_ai:12b48c8f43` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 164, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `overbought_bucket` | `overbought_normal` | 207 | 6 | 0.3563 | -1.419 | 0.0 | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 420 | 5 | 0.5119 | -1.482 | 0.0 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_high` | 241 | 5 | 0.5119 | -1.482 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1106 | 5 | 0.5119 | -1.482 | 0.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | 0.5119 | -1.482 | 0.0 | `hold_sample` |
| `stale_bucket` | `stale_high` | 172 | 4 | 0.5305 | -1.4875 | 0.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 228 | 4 | 0.2325 | -1.386 | 0.0 | `source_quality_workorder` |
| `score_band` | `score_lt60` | 1098 | 3 | 0.5467 | -1.4867 | 0.0 | `source_quality_workorder` |
| `strength_bucket` | `weak_strength_momentum` | 130 | 3 | 0.4318 | -1.4867 | 0.0 | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 831 | 2 | 0.6321 | -1.475 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_1000_1200` | 41 | 2 | 0.6038 | -1.485 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 380 | 2 | 0.6038 | -1.485 | 0.0 | `source_quality_workorder` |
| `chosen_action` | `WAIT_REQUOTE` | 693 | 1 | -0.422 | -1.1039 | 0.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1255 | 1 | -0.422 | -1.1039 | 0.0 | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 161 | 1 | 0.4374 | -1.46 | 0.0 | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 34 | 1 | -0.422 | -1.1039 | 0.0 | `hold_sample` |
| `liquidity_bucket` | `liquidity_mid` | 13 | 1 | -0.422 | -1.1039 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_high|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 2 | 1 | 0.4819 | -1.49 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_high|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | 0.4374 | -1.46 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_mid|overbought=overbought_normal|time=time_0900_1000` | 1 | 1 | -0.422 | -1.1039 | 0.0 | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 109, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 254 | 10 | 0.4295 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 36 | 10 | 0.4295 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 286 | 10 | 0.4295 | `keep_collecting` |
| `latency_reason` | `scalp_live_simulator` | 36 | 10 | 0.4295 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 36 | 10 | 0.4295 | `keep_collecting` |
| `latency_state` | `simulated` | 36 | 10 | 0.4295 | `keep_collecting` |
| `broker_order_forbidden` | `true` | 254 | 10 | 0.4295 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 36 | 10 | 0.4295 | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 29 | 7 | -0.0608 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 28 | 6 | 0.4995 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 28 | 6 | 0.4995 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 239 | 6 | 0.4995 | `source_quality_workorder` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 28 | 6 | 0.4995 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 28 | 6 | 0.4995 | `keep_collecting` |
| `liquidity_bucket` | `below_min_liquidity` | 8 | 4 | 0.3246 | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 8 | 4 | 0.3246 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_pre_submit_liquidity_guard_would_block` | 8 | 4 | 0.3246 | `keep_collecting` |
| `liquidity_guard_action` | `would_block` | 8 | 4 | 0.3246 | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 8 | 4 | 0.3246 | `source_quality_workorder` |
| `would_limit_fill` | `false` | 297 | 3 | 0.4169 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 7 | 3 | 1.5736 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 17 | 3 | 0.4169 | `source_quality_workorder` |
| `would_limit_fill` | `true` | 11 | 3 | 0.582 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_10s_plus` | 5 | 2 | 0.6167 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 8 | 2 | 0.6543 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_1_3s` | 43 | 1 | 4.1198 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 27 | 1 | -4.055 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=true|submitted=false` | 3 | 1 | 0.4374 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 0.1637 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_10s_plus|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | 1.0697 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | 4.1198 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_pre_submit_liquidity_guard_would_block|revalidation=ok_or_unflagged|quote_age=quote_age_3_10s|liquidity=below_min_liquidity|liquidity_guard=would_block|overbought=overbought_ok|latency=simulated|refresh=sim_submit_path_not_applicable|fill=would_limit_fill_unknown|submitted=false` | 2 | 1 | -4.055 | `source_quality_workorder` |
| `latency_state` | `caution` | 27 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 27 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 225 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 22, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `held_bucket` | `held_not_applicable_at_start` | 36 | 10 | -0.55 | `hold_no_edge` |
| `holding_source_stage` | `scalp_sim_holding_started` | 36 | 10 | -0.55 | `hold_no_edge` |
| `holding_action` | `WAIT` | 35 | 9 | -0.4301 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 8 | 8 | -0.8098 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 7 | 7 | -0.6927 | `hold_sample` |
| `holding_action` | `holding_action_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | 2.3727 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_pos080_pos150|held=held_not_applicable_at_start` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_not_applicable_at_start|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 1 | 1 | -1.6295 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 6 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 6 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 26 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 4 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 26 | 26 | -0.9763 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 24 | 24 | -0.9234 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 24 | 24 | -0.9234 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 24 | 24 | -0.9234 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 19 | 19 | -1.0226 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 11 | 11 | -0.3423 | `hold_sample` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 9 | 9 | -0.5529 | `hold_no_edge` |
| `exit_outcome` | `COMPLETED` | 6 | 6 | -0.1725 | `hold_sample` |
| `exit_outcome` | `MISSED_UPSIDE` | 6 | 6 | -0.2336 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 6 | 6 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 5 | 5 | -0.4918 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 5 | 5 | -0.546 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 4 | 4 | -0.4773 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `NEUTRAL` | 2 | 2 | -1.0896 | `hold_sample` |
| `exit_rule` | `scalp_soft_stop_pct` | 2 | 2 | -1.7473 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 2 | 2 | 0.4889 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 1 | 1 | -1.395 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `profit_band` | `profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.5496 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=MISSED_UPSIDE|profit=profit_lt_neg070` | 1 | 1 | -1.8651 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_soft_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -1.6295 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_pos080_pos150` | 1 | 1 | -1.395 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=MISSED_UPSIDE|profit=profit_neg010_pos080` | 1 | 1 | 2.3727 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 51 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 51 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 34 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 34 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 17 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 17 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 34 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 17 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 158, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 563 | 563 | None | -0.6408 | 0.0888 | `hold_sample` |
| `qty_reason` | `qty_none` | 563 | 563 | None | -0.6408 | 0.0888 | `hold_sample` |
| `time_bucket` | `time_unknown` | 563 | 563 | None | -0.6408 | 0.0888 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 559 | 559 | None | -0.6409 | 0.0876 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 543 | 543 | None | -0.6439 | 0.0921 | `hold_sample` |
| `arm` | `AVG_DOWN` | 513 | 513 | None | -0.7619 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 510 | 510 | None | -0.7467 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 454 | 454 | None | -0.7868 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 292 | 292 | None | -0.6326 | 0.0856 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 257 | 257 | None | -0.4405 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 244 | 244 | None | -1.1357 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 205 | 205 | None | -0.609 | 0.1268 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 160 | 160 | None | -0.764 | 0.05 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 130 | 130 | None | -0.7376 | 0.0077 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 111 | 111 | None | -0.7278 | 0.0631 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 110 | 110 | None | -0.5316 | 0.1364 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 81 | 81 | None | -0.4968 | 0.1481 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 72 | 72 | None | -0.2013 | 0.4861 | `hold_sample` |
| `arm` | `PYRAMID` | 50 | 50 | None | 0.6018 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 50 | 50 | None | 0.6018 | 1.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 6 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 6 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 12 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 6 | 6 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 8 | 4 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 6 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 6 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 6 | 0 | None | None | None | `hold_sample` |

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
