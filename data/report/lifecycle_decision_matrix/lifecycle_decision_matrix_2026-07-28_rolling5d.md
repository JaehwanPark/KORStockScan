# Lifecycle Decision Matrix - 2026-07-28

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-28_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `434`
- source_rows_total: `865`
- retained_rows: `434`
- dropped_rows_by_source: `{}`
- joined_rows: `13`
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
- lifecycle_flow_bucket_count: `34`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 357 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `submit` | 61 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `holding` | 3 | 0 | None | None | `pass` | `NO_CHANGE` | False |
| `scale_in` | 10 | 10 | -1.0202 | 0.38 | `pass` | `NO_CHANGE` | False |
| `exit` | 3 | 3 | -0.1725 | 0.1 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 34, 'complete_flow_count': 0, 'incomplete_flow_count': 162, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 8 | 8 | -1.3678 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 2 | 2 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2 | 2 | 0.37 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:e48ea83ea5` | 1 | 1 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8a9ce220d7` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:6376c75255` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:ed61640e60` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:6ac4da565f` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 6 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:c50d2ff605` | 9 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:daa7e36576` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 24 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f51f5dbd6a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:7b1e064efb` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 111, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `BUY_DEFENSIVE` | 23 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 7 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 152 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 36 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_STALE` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 138 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `ai_confirmed` | 54 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `blocked_ai_score` | 4 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 357 | 0 | None | None | None | `source_quality_workorder` |
| `stale_bucket` | `fresh` | 132 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_high` | 123 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_mid` | 6 | 0 | None | None | None | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 228 | 0 | None | None | None | `source_quality_workorder` |
| `strength_bucket` | `neutral_strength_momentum` | 230 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_chase_risk` | 9 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_normal` | 74 | 0 | None | None | None | `hold_sample` |
| `overbought_bucket` | `overbought_not_available` | 225 | 0 | None | None | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_watch` | 49 | 0 | None | None | None | `hold_sample` |
| `strength_bucket` | `risk_unknown` | 55 | 0 | None | None | None | `source_quality_workorder` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 299 | 0 | None | None | None | `source_quality_workorder` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 54, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `latency_state` | `caution` | 12 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 12 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 46 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 1 | 0 | None | `keep_collecting` |
| `actual_order_submitted` | `false` | 46 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 15 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 61 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 46 | 0 | None | `keep_collecting` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 61 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 61 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `observer_quote:observer_quote_fresh` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `observer_quote_refresh_applied` | 1 | 0 | None | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 60 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `orderbook_stability_observer` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 61 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 61 | 0 | None | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 61 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_not_available_pre_submit` | 46 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_1_3s` | 14 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_lt1s` | 1 | 0 | None | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 46 | 0 | None | `source_quality_workorder` |
| `pre_submit_refresh_age_bucket` | `refresh_age_1_3s` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_lt1s` | 45 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `refresh_age_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_attempted` | 46 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_attempted_not_applied` | 1 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_failed_quote_stale` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `refresh_not_attempted_or_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_attempted` | `refresh_not_attempted_or_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_not_attempted_or_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `refresh_reason_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `quote_freshness_resolution_state` | `refresh_resolved_quote_freshness` | 45 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `refresh_source_not_instrumented` | 15 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `resolved_price` | 14 | 0 | None | `keep_collecting` |
| `latency_state` | `safe` | 3 | 0 | None | `keep_collecting` |
| `latency_reason` | `safe_normal_entry_allowed` | 3 | 0 | None | `keep_collecting` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_failed_quote_stale|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=latency_block|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=danger|refresh=refresh_resolved_quote_freshness|fill=false|submitted=false` | 45 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=order_bundle_submitted|revalidation=ok_or_unflagged|quote_age=quote_age_1_3s|liquidity=liquidity_not_available|liquidity_guard=liquidity_guard_unknown|overbought=overbought_not_available|latency=caution|refresh=refresh_not_attempted_or_not_instrumented|fill=false|submitted=true` | 12 | 0 | None | `source_quality_workorder` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 7, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_180_600s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_180_600s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 5, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.1725 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 32, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 10 | 10 | None | -1.178 | 0.2 | `hold_sample` |
| `qty_reason` | `qty_none` | 10 | 10 | None | -1.178 | 0.2 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 10 | 10 | None | -1.178 | 0.2 | `hold_sample` |
| `time_bucket` | `time_unknown` | 10 | 10 | None | -1.178 | 0.2 | `hold_sample` |
| `arm` | `AVG_DOWN` | 8 | 8 | None | -1.5588 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 8 | 8 | None | -1.5588 | 0.0 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 7 | 7 | None | -1.6614 | 0.1429 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 6 | 6 | None | -0.8667 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_1` | 5 | 5 | None | -0.54 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 4 | 4 | None | -1.7975 | 0.25 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 4 | 4 | None | -1.645 | 0.5 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | None | -2.6625 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 4 | 4 | None | -0.455 | 0.0 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 4 | 4 | None | -1.645 | 0.5 | `hold_sample` |
| `arm` | `PYRAMID` | 2 | 2 | None | 0.345 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2 | 2 | None | 0.345 | 1.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 2 | 2 | None | -0.655 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 2 | 2 | None | -0.275 | 0.5 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 2 | 2 | None | 0.195 | 0.5 | `hold_sample` |
| `blocker_reason` | `probe_expand_forbidden` | 2 | 2 | None | -3.635 | 0.0 | `hold_sample` |

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
