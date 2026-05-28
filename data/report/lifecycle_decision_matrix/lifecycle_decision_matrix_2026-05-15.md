# Lifecycle Decision Matrix - 2026-05-15

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-15`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `71`
- source_rows_total: `71`
- retained_rows: `71`
- dropped_rows_by_source: `{}`
- joined_rows: `66`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `7` / `5`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `21`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `4`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 65, 'missing_exit': 65, 'missing_submit': 63, 'missing_holding': 63}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 2 | 1 | -1.83 | 0.05 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 2 | 1 | -1.83 | 0.05 | `hold_sample` | `EXIT` | False |
| `scale_in` | 67 | 64 | -3.3822 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 65, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 71, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 2, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 2, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 2}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 67, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 67}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 65, 'missing_exit': 65, 'missing_submit': 63, 'missing_holding': 63}, 'bucket_count': 4, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 62 | 61 | -0.813 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:6ea1243a3e` | 1 | 1 | -1.83 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | -55.622 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bbed60de0b` | 1 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- none

## Submit Bucket Attribution

- decision_authority: `adm_ldm_submit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'submit_rows': 2, 'bucket_count': 22, 'contract_gap_count': 1, 'workorder_count': 1, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 2 | 1 | -1.83 | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=true|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_entry_submit_revalidation_warning|revalidation=warning_stale_context_or_quote|quote_age=quote_age_3_10s|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=would_limit_fill_unknown|submitted=false` | 1 | 1 | -1.83 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `price_below_bid_bucket` | `below_bid_20bps_plus` | 1 | 1 | -1.83 | `keep_collecting` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `defensive_order_price` | 1 | 1 | -1.83 | `keep_collecting` |
| `price_resolution_bucket` | `price_resolution_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_3_10s` | 1 | 1 | -1.83 | `keep_collecting` |
| `quote_age_bucket` | `quote_age_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 1 | 0 | None | `keep_collecting` |
| `revalidation_state` | `warning_stale_context_or_quote` | 1 | 1 | -1.83 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_entry_submit_revalidation_warning` | 1 | 1 | -1.83 | `keep_collecting` |
| `would_limit_fill` | `true` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `would_limit_fill_unknown` | 1 | 1 | -1.83 | `source_quality_workorder` |

### Submit Bucket Workorders

- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 2, 'source_row_count': 2, 'bucket_count': 7, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': -1.83, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'not_applicable': 2, 'join_gap': 4, 'missing_source_field': 2}, 'workorder_count': 5, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` | 1 | 1 | -1.83 | `source_quality_workorder` |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 2 | 1 | -1.83 | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 2 | 1 | -1.83 | `hold_sample` |
| `profit_band` | `profit_lt_neg070` | 1 | 1 | -1.83 | `hold_sample` |
| `profit_band` | `profit_unknown` | 1 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_lt_neg070|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_5`: `profit_band` / `profit_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

## Exit Bucket Attribution

- decision_authority: `adm_ldm_exit_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'exit_rows': 0, 'source_row_count': 0, 'bucket_count': 0, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |

### Exit Bucket Attribution Workorders

- none

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 67, 'bucket_count': 62, 'actionable_bucket_count': 21, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 64, 'PYRAMID': 3}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 44 | 44 | -0.7848 | -0.8764 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 14 | 14 | -0.8847 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_lt60` | 3 | 3 | -55.622 | -69.47 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 2 | 2 | -0.884 | -0.99 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_60_62` | 1 | 1 | -0.91 | -0.91 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 3 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 67 | 64 | -3.3822 | -4.1184 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 64 | 63 | -2.1767 | -2.6108 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 3 | 1 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 59 | 59 | -2.2867 | -2.7502 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4 | 4 | -0.555 | -0.555 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 1 | 1 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PRICE_GUARD` | 2 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 1 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `scale_in_probe_blocked` | 23 | 23 | -0.777 | -0.9839 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 8 | 8 | -0.4675 | -0.4675 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ai_not_recovering` | 3 | 3 | -0.3033 | -0.3033 | 0.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.37)` | 3 | 3 | -1.37 | -1.37 | 0.0 | `hold_sample` |
| `blocker_reason` | `scale_in_gate_blocked` | 3 | 3 | -0.5353 | -0.6867 | 0.0 | `hold_sample` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 3 | 3 | -55.622 | -69.47 | 0.0 | `hold_sample` |
| `held_bucket` | `held_180_600s` | 25 | 25 | -0.7251 | -0.796 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 23 | 23 | -1.2455 | -1.4004 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 11 | 11 | -0.2145 | -0.2364 | 0.0 | `hold_no_edge` |
| `held_bucket` | `held_lt020s` | 5 | 5 | -33.4652 | -41.774 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 37 | 34 | -0.845 | -0.845 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 25 | 25 | -0.8222 | -1.0452 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 5 | 5 | -33.4352 | -41.744 | 0.0 | `candidate_tighten_or_exclude` |
| `price_guard_reason` | `price_guard_none` | 65 | 64 | -3.3822 | -4.1184 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 40 | 40 | -5.1832 | -6.3412 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 21 | 21 | -0.4271 | -0.4652 | 0.0 | `candidate_tighten_or_exclude` |
| `qty_reason` | `qty_none` | 66 | 64 | -3.3822 | -4.1184 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_unknown` | 33 | 30 | -6.2577 | -7.8283 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_3` | 17 | 17 | -0.7418 | -0.7418 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_2` | 12 | 12 | -1.0 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_unknown` | 67 | 64 | -3.3822 | -4.1184 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_70p` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `scale_in_probe_blocked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `held_bucket` / `held_180_600s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `held_bucket` / `held_600_1800s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `peak_profit_band` / `peak_zero_pos080` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_14`: `price_guard_reason` / `price_guard_none` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_15`: `profit_band` / `profit_lt_neg070` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `scale_in_probe_blocked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `add_judgment_locked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `held_bucket` / `held_180_600s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `held_bucket` / `held_600_1800s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `held_bucket` / `held_lt020s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 0, 'bucket_count': 0, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {}}`

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
