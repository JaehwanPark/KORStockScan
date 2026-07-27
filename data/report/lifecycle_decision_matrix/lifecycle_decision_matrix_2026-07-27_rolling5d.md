# Lifecycle Decision Matrix - 2026-07-27

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-27_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `704`
- source_rows_total: `1913`
- retained_rows: `704`
- dropped_rows_by_source: `{}`
- joined_rows: `113`
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
- lifecycle_flow_bucket_count: `43`
- lifecycle_flow_complete_count: `7`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0215`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 477 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `submit` | 83 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `holding` | 15 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `scale_in` | 102 | 102 | -0.6077 | 0.9637 | `pass` | `NO_CHANGE` | False |
| `exit` | 27 | 11 | -0.697 | 0.2833 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 43, 'complete_flow_count': 7, 'incomplete_flow_count': 319, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 100 | 100 | -0.6238 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:ac760bc3a4` | 6 | 6 | -0.8717 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2 | 2 | 0.195 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:57aa592422` | 1 | 1 | -0.96 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:e48ea83ea5` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:6376c75255` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ed61640e60` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:6ac4da565f` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:f2ff621987` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 8 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 9 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 24 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f51f5dbd6a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:6ce17fe9aa` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 130, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 10 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 22 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 5 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 220 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 37 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 180 | 0 | None | None | None | `hold_sample` |
| `strength_bucket` | `WEAK` | 10 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `ai_confirmed` | 67 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `blocked_ai_score` | 17 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 477 | 0 | None | None | None | `hold_sample` |
| `stale_bucket` | `fresh` | 133 | 0 | None | None | None | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 10 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 186 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_mid` | 6 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 275 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_state_normal` | 10 | 0 | None | None | None | `hold_sample` |
| `strength_bucket` | `neutral_strength_momentum` | 287 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_chase_risk` | 8 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 86, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `liquidity_bucket` | `below_min_liquidity` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `caution` | 10 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 10 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 54 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 15 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_order_price` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 2 | 0 | None | `keep_collecting` |
| `actual_order_submitted` | `false` | 68 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 15 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 80 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 54 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 2 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 71 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 71 | 0 | None | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 11 | 0 | None | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 12 | 0 | None | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 78 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 15 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 71 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 71 | 0 | None | `keep_collecting` |
| `overbought_bucket` | `overbought_ok` | 11 | 0 | None | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 71 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_not_available_pre_submit` | 54 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 11 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_10s_plus` | 1 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 12 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_3_10s` | 5 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 65 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `refresh_age_3_10s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 53 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 17 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 54 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 2 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_failed_quote_stale` | 2 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 17 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_not_attempted_or_not_instrumented` | 17 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_not_attempted_or_not_instrumented` | 17 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `refresh_reason_not_instrumented` | 17 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 12, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `holding_action` | `WAIT` | 12 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `held_bucket` | `held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_holding_started` | 12 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_not_applicable_at_start|held=held_not_applicable_at_start` | 12 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 19, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 8 | 8 | -0.8938 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 7 | 7 | -0.9214 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 7 | 7 | -0.9214 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | -0.3044 | `hold_sample` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010` | 1 | 1 | -0.7 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 16 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 16 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 12 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 12 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_panic_context_warning` | 4 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_context_warning_not_applicable` | 4 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 12 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_panic_context_warning|rule=scalp_sim_panic_context_warning_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 4 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 66, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 102 | 102 | None | -0.6792 | 0.0196 | `hold_sample` |
| `qty_reason` | `qty_none` | 102 | 102 | None | -0.6792 | 0.0196 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 102 | 102 | None | -0.6792 | 0.0196 | `hold_sample` |
| `time_bucket` | `time_unknown` | 102 | 102 | None | -0.6792 | 0.0196 | `hold_sample` |
| `arm` | `AVG_DOWN` | 100 | 100 | None | -0.6962 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 100 | 100 | None | -0.6962 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 82 | 82 | None | -0.7088 | 0.0244 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 75 | 75 | None | -0.6859 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 63 | 63 | None | -0.4608 | 0.0 | `hold_sample` |
| `ai_score_source` | `live` | 49 | 49 | None | -0.6569 | 0.0 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 35 | 35 | None | -1.1557 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 33 | 33 | None | -0.6488 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 32 | 32 | None | -0.5056 | 0.0312 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 31 | 31 | None | -0.8213 | 0.0322 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 23 | 23 | None | -0.6982 | 0.0435 | `hold_sample` |
| `ai_score_source` | `score_field_backfilled` | 21 | 21 | None | -0.8271 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 20 | 20 | None | -0.558 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 17 | 17 | None | -0.42 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-0.35)` | 8 | 8 | None | -0.35 | 0.0 | `hold_sample` |
| `blocker_reason` | `scalp_sim_panic_scale_in_blocked` | 8 | 8 | None | -0.8237 | 0.0 | `hold_sample` |

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
| `overnight_action` | `SELL_TODAY` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `SELL_TODAY` | 3 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `price_source` | `buy_price_fallback` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `confidence_band` | `confidence_070p` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `stage` | `exit` | 3 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_quality_gate` | `overnight_decision_coverage` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 6 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 4 | 2 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
| `overnight_status` | `HOLD_OVERNIGHT` | 3 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 3 | 0 | None | None | None | `hold_sample` |
| `stage` | `holding` | 3 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | None | None | `hold_sample` |

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
