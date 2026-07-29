# Lifecycle Decision Matrix - 2026-07-29

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-07-29_rolling5d`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `447`
- source_rows_total: `881`
- retained_rows: `447`
- dropped_rows_by_source: `{}`
- joined_rows: `103`
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
- lifecycle_flow_bucket_count: `37`
- lifecycle_flow_complete_count: `3`
- lifecycle_flow_complete_breakdown direct/adm/fallback: `None` / `None` / `None`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0127`
- incomplete_flow_reason_counts: `{}`
- bucket_directed_sim_probe: `{}`
- lifecycle_ai_context_feedback: `{}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 274 | 3 | -0.8198 | 0.0118 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 62 | 3 | -0.8198 | 0.045 | `pass` | `NO_CHANGE` | False |
| `holding` | 6 | 3 | -0.8757 | 0.225 | `pass` | `EXIT` | False |
| `scale_in` | 86 | 85 | -0.1687 | 0.9518 | `pass` | `NO_CHANGE` | False |
| `exit` | 19 | 9 | -0.5972 | 0.2464 | `pass` | `EXIT` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `aggregated_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `None`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 37, 'complete_flow_count': 3, 'incomplete_flow_count': 234, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 43 | 43 | 0.411 | `candidate_recovery_or_relax` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 43 | 42 | -0.7621 | `candidate_tighten_or_exclude` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:62b3401904` | 3 | 3 | -0.1725 | `hold_no_edge` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:f44ea1e4fd` | 2 | 2 | -1.28 | `candidate_tighten_or_exclude` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:cb6ed22b69` | 1 | 1 | 0.33 | `candidate_recovery_or_relax` | `pass` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:661dd5007a` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:306834dafc` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_sc:01a26e930a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_sc:8a9ce220d7` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:6376c75255` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_ai_c:2315da1c23` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:425fb814b4` | 3 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:54101985e8` | 4 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:daa7e36576` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:81a1a398fd` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_70p_source_scal:07390fbd3e` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f2f2f3d14e` | 14 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:f51f5dbd6a` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_:de60314e2b` | 2 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_blo:70a865069d` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `aggregated_entry_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 118, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 11 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `liquidity_bucket` | `liquidity_not_available` | 175 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 165 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `strength_bucket` | `risk_context_not_available` | 10 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `source_stage` | `scalp_sim_entry_ai_price_skip_order` | 10 | 3 | -0.8198 | -0.89 | 0.3333 | `hold_sample` |
| `score_band` | `score_lt60` | 229 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `stale_bucket` | `stale_not_available` | 58 | 3 | -0.8198 | -0.89 | 0.3333 | `source_quality_workorder` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -0.6883 | -1.42 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200` | 8 | 2 | -0.6883 | -1.42 | 0.0 | `hold_sample` |
| `time_bucket` | `time_1000_1200` | 72 | 2 | -0.6883 | -1.42 | 0.0 | `source_quality_workorder` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | -1.083 | 0.17 | 1.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_entry_ai_price_skip_order|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000` | 1 | 1 | -1.083 | 0.17 | 1.0 | `hold_sample` |
| `time_bucket` | `time_0900_1000` | 86 | 1 | -1.083 | 0.17 | 1.0 | `source_quality_workorder` |
| `chosen_action` | `ALLOW_LEVEL1_RISK_OFF_ENTRY` | 9 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_DEFENSIVE` | 24 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `BUY_NOW` | 8 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `NO_BUY_AI` | 122 | 0 | None | None | None | `source_quality_workorder` |
| `chosen_action` | `SKIP_STALE` | 2 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 98 | 0 | None | None | None | `hold_sample` |
| `strength_bucket` | `WEAK` | 9 | 0 | None | None | None | `hold_sample` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `aggregated_submit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- summary: `{'bucket_count': 82, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 38 | 3 | -0.8198 | `keep_collecting` |
| `would_limit_fill` | `false` | 62 | 3 | -0.8198 | `keep_collecting` |
| `liquidity_bucket` | `liquidity_ok` | 3 | 3 | -0.8198 | `keep_collecting` |
| `price_below_bid_bucket` | `not_below_bid` | 3 | 3 | -0.8198 | `keep_collecting` |
| `revalidation_state` | `ok_or_unflagged` | 61 | 3 | -0.8198 | `keep_collecting` |
| `overbought_bucket` | `overbought_context_missing` | 3 | 3 | -0.8198 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 3 | 3 | -0.8198 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 37 | 3 | -0.8198 | `source_quality_workorder` |
| `latency_reason` | `scalp_live_simulator` | 3 | 3 | -0.8198 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_age_bucket` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_applied` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_attempted` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_reason` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `pre_submit_refresh_source` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `quote_freshness_resolution_state` | `sim_submit_path_not_applicable` | 3 | 3 | -0.8198 | `keep_collecting` |
| `latency_state` | `simulated` | 3 | 3 | -0.8198 | `keep_collecting` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_ok|liquidity_guard=would_pass|overbought=overbought_context_missing|latency=simulated|refresh=sim_submit_path_not_applicable|fill=false|submitted=false` | 3 | 3 | -0.8198 | `source_quality_workorder` |
| `broker_order_forbidden` | `true` | 38 | 3 | -0.8198 | `keep_collecting` |
| `liquidity_guard_action` | `would_pass` | 3 | 3 | -0.8198 | `keep_collecting` |
| `overbought_guard_action` | `would_pass` | 3 | 3 | -0.8198 | `keep_collecting` |
| `latency_state` | `caution` | 19 | 0 | None | `keep_collecting` |
| `latency_reason` | `caution_normal_entry_allowed` | 19 | 0 | None | `keep_collecting` |
| `latency_state` | `danger` | 36 | 0 | None | `keep_collecting` |
| `price_resolution_bucket` | `defensive_limit` | 6 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `entry_submit_revalidation_block` | 1 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `false` | 24 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `latency_block` | 34 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_spread_relief_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_reason` | `latency_true_ofi_false_negative_direct_canary_normal_override` | 1 | 0 | None | `keep_collecting` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 59 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_not_available` | 59 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_reason` | `observer_quote:observer_quote_fresh` | 1 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_applied` | `observer_quote_refresh_applied` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `order_bundle_submitted` | 24 | 0 | None | `keep_collecting` |
| `pre_submit_refresh_source` | `orderbook_stability_observer` | 1 | 0 | None | `keep_collecting` |
| `overbought_guard_action` | `overbought_guard_unknown` | 59 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_not_available` | 59 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `aggregated_holding_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 14, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `holding_action` | `WAIT` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_not_applicable_at_start` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `holding_source_stage` | `scalp_sim_holding_started` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 2 | 2 | -1.0724 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_lt_neg070|held=held_not_applicable_at_start` | 2 | 2 | -1.0724 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=WAIT|profit=profit_neg010_pos080|held=held_not_applicable_at_start` | 1 | 1 | -0.4823 | `hold_sample` |
| `holding_action` | `SELL_TODAY` | 3 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `held_bucket` | `held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 3 | 0 | None | `hold_sample` |
| `holding_source_stage` | `scalp_sim_overnight_decision` | 3 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s` | 1 | 0 | None | `hold_sample` |
| `combo_holding_flow` | `source=scalp_sim_overnight_decision|action=SELL_TODAY|profit=profit_neg070_neg010|held=held_600_1800s_plus` | 2 | 0 | None | `hold_sample` |

### Holding Bucket Attribution Workorders

- none

## Exit Bucket Attribution

- decision_authority: `aggregated_exit_bucket_attribution_source_only`
- primary_decision_metric: `None`
- allowed_runtime_apply: `False`
- summary: `{'bucket_count': 25, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `profit_band` | `profit_lt_neg070` | 4 | 4 | -1.1762 | `candidate_tighten_or_exclude` |
| `exit_outcome` | `COMPLETED` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_partial_exit` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_source_stage` | `scalp_sim_overnight_sell_today` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_partial_exit` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `scalp_sim_partial_sell_order_assumed_filled` | 3 | 3 | -0.7433 | `candidate_tighten_or_exclude` |
| `exit_source_stage` | `sim_post_sell_evaluation` | 3 | 3 | -0.8757 | `candidate_tighten_or_exclude` |
| `combo_exit_result` | `source=scalp_sim_overnight_sell_today|rule=scalp_sim_overnight_sell_today|outcome=COMPLETED|profit=profit_neg070_neg010` | 3 | 3 | -0.1725 | `hold_sample` |
| `exit_outcome` | `GOOD_EXIT` | 2 | 2 | -0.9458 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 2 | 2 | -0.0761 | `hold_sample` |
| `exit_rule` | `scalp_preset_hard_stop_pct` | 2 | 2 | -1.0724 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070` | 2 | 2 | -1.28 | `hold_sample` |
| `exit_outcome` | `NEUTRAL` | 1 | 1 | -0.7356 | `hold_sample` |
| `exit_rule` | `scalp_trailing_take_profit` | 1 | 1 | -0.4823 | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg010_pos080` | 1 | 1 | 0.33 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=GOOD_EXIT|profit=profit_lt_neg070` | 1 | 1 | -1.4093 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_preset_hard_stop_pct|outcome=NEUTRAL|profit=profit_lt_neg070` | 1 | 1 | -0.7356 | `hold_sample` |
| `combo_exit_result` | `source=sim_post_sell_evaluation|rule=scalp_trailing_take_profit|outcome=GOOD_EXIT|profit=profit_neg010_pos080` | 1 | 1 | -0.4823 | `hold_sample` |
| `exit_outcome` | `outcome_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |
| `profit_band` | `profit_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |
| `exit_source_stage` | `scalp_sim_euphoria_context_noop` | 10 | 0 | None | `hold_sample` |
| `exit_rule` | `scalp_sim_euphoria_context_noop_not_applicable` | 10 | 0 | None | `hold_sample` |
| `combo_exit_result` | `source=scalp_sim_euphoria_context_noop|rule=scalp_sim_euphoria_context_noop_not_applicable|outcome=outcome_not_applicable_context_noop|profit=profit_not_applicable_context_noop` | 10 | 0 | None | `hold_sample` |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `aggregated_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `stage_ev_composite_pct`
- summary: `{'bucket_count': 52, 'complete_flow_count': 0, 'incomplete_flow_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `price_guard_reason` | `price_guard_none` | 86 | 85 | None | -0.2325 | 0.5058 | `hold_sample` |
| `qty_reason` | `qty_none` | 85 | 85 | None | -0.2325 | 0.5058 | `hold_sample` |
| `ai_score_band` | `score_lt60` | 85 | 85 | None | -0.2325 | 0.5058 | `hold_sample` |
| `time_bucket` | `time_unknown` | 86 | 85 | None | -0.2325 | 0.5058 | `hold_sample` |
| `supply_pass_bucket` | `supply_pass_unknown` | 63 | 62 | None | -0.0718 | 0.6936 | `hold_sample` |
| `ai_score_source` | `neutral_unusable` | 54 | 54 | None | 0.0191 | 0.7407 | `hold_sample` |
| `peak_profit_band` | `peak_zero_pos080` | 49 | 49 | None | 0.15 | 0.8775 | `hold_sample` |
| `arm` | `PYRAMID` | 43 | 43 | None | 0.3688 | 1.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 43 | 43 | None | 0.3688 | 1.0 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 43 | 43 | None | 0.3688 | 1.0 | `hold_sample` |
| `arm` | `AVG_DOWN` | 43 | 42 | None | -0.8481 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 43 | 42 | None | -0.8481 | 0.0 | `hold_sample` |
| `blocker_reason` | `profit_not_enough` | 41 | 41 | None | 0.3668 | 1.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 31 | 31 | None | 0.2361 | 0.8387 | `hold_sample` |
| `ai_score_source` | `not_evaluated_no_ai_score_source` | 25 | 25 | None | -0.6944 | 0.08 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 24 | 24 | None | -0.1858 | 0.6667 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 24 | 24 | None | -1.2321 | 0.0 | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 24 | 23 | None | -0.6657 | 0.0 | `hold_sample` |
| `profit_band` | `profit_neg070_neg010` | 18 | 18 | None | -0.3361 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 17 | 17 | None | -0.7518 | 0.0588 | `hold_sample` |

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
| `held_bucket` | `held_600_1800s` | 2 | 1 | -0.1725 | -0.23 | 0.0 | `hold_sample` |
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
