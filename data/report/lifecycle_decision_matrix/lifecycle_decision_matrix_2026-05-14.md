# Lifecycle Decision Matrix - 2026-05-14

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-14`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `2202`
- source_rows_total: `2202`
- retained_rows: `2202`
- dropped_rows_by_source: `{}`
- joined_rows: `1137`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `5` / `3`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `16`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `3`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 1147, 'missing_exit': 1147, 'missing_submit': 1146, 'missing_holding': 1146}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 1 | 1 | 0.55 | 0.1 | `hold_sample` | `ALLOW_SUBMIT` | False |
| `holding` | 1 | 1 | 0.55 | 0.1 | `hold_sample` | `HOLD` | False |
| `scale_in` | 2200 | 1135 | -0.0159 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1147, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 2202, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 2200, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 2200}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 1147, 'missing_exit': 1147, 'missing_submit': 1146, 'missing_holding': 1146}, 'bucket_count': 3, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 1141 | 1135 | -0.0159 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_combo_submit_quality_s:bbed60de0b` | 1 | 1 | 0.55 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 5 | 0 | None | `hold_sample` | `hold_sample_or_incomplete_flow` |

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
- summary: `{'submit_rows': 1, 'bucket_count': 15, 'contract_gap_count': 2, 'workorder_count': 2, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1 | 1 | 0.55 | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 1 | 1 | 0.55 | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 1 | 1 | 0.55 | `keep_collecting` |
| `would_limit_fill` | `false` | 1 | 1 | 0.55 | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_post_submit_contract_gap_review`: `post_submit_contract_gap` / `price_revalidation_or_submit_state_missing` -> `price_revalidation_or_submit_state_missing`
- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 5, 'source_quality_adjusted_ev_pct': 0.55, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'not_applicable': 2, 'missing_source_field': 2}, 'workorder_count': 3, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 1 | 1 | 0.55 | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1 | 1 | 0.55 | `hold_sample` |
| `profit_band` | `profit_neg010_pos080` | 1 | 1 | 0.55 | `hold_sample` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_neg010_pos080|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

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
- summary: `{'scale_in_rows': 2200, 'bucket_count': 216, 'actionable_bucket_count': 16, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 1920, 'PYRAMID': 280}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 963 | 963 | -0.0158 | -0.101 | 0.3988 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 139 | 139 | -0.0313 | -0.1181 | 0.3165 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 18 | 18 | -0.0128 | -0.1122 | 0.7778 | `hold_no_edge` |
| `ai_score_band` | `score_lt60` | 8 | 8 | 0.0885 | -0.0025 | 0.75 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 7 | 7 | 0.1451 | 0.0486 | 0.8571 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 1065 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 2200 | 1135 | -0.0159 | -0.1017 | 0.4 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 1920 | 1135 | -0.0159 | -0.1017 | 0.4 | `hold_no_edge` |
| `arm` | `PYRAMID` | 280 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 980 | 980 | 0.0362 | -0.0631 | 0.4633 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 155 | 155 | -0.3457 | -0.3457 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `QTY_GUARD` | 1065 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 286 | 286 | -0.2284 | -0.2284 | 0.2622 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 233 | 233 | 0.0538 | -0.2033 | 0.2876 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 215 | 215 | 0.2466 | 0.0755 | 0.586 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(1.16)` | 45 | 45 | 1.16 | 1.16 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(0.03)` | 38 | 38 | 0.03 | 0.03 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.16)` | 37 | 37 | 0.16 | 0.16 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.29)` | 25 | 25 | 0.29 | 0.29 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.42)` | 19 | 19 | 0.42 | 0.42 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.88)` | 14 | 14 | -0.88 | -0.88 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.01)` | 13 | 13 | -1.01 | -1.01 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 11 | 11 | -0.75 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.14)` | 9 | 9 | -1.14 | -1.14 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.27)` | 8 | 8 | -1.27 | -1.27 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 1035 | 1035 | 0.0346 | -0.0555 | 0.4213 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s` | 62 | 62 | -0.4393 | -0.469 | 0.2903 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 24 | 24 | -0.8852 | -0.9671 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 12 | 12 | -0.4163 | -0.4358 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 1751 | 686 | -0.12 | -0.12 | 0.3805 | `hold_no_edge` |
| `peak_profit_band` | `peak_pos080_pos150` | 384 | 384 | 0.2072 | -0.0347 | 0.4271 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 36 | 36 | -0.6844 | -0.7917 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `blocker_reason` / `pnl_out_of_range(1.16)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_3`: `blocker_reason` / `pnl_out_of_range(0.42)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_4`: `blocker_reason` / `pnl_out_of_range(-0.88)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `pnl_out_of_range(-1.01)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-0.75)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `held_bucket` / `held_600_1800s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `held_bucket` / `held_180_600s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `held_bucket` / `held_020_180s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `blocker_reason` / `pnl_out_of_range(1.16)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_reason` / `pnl_out_of_range(0.42)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `pnl_out_of_range(-0.88)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `pnl_out_of_range(-1.01)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-0.75)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-1.14)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-1.27)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `held_bucket` / `held_600_1800s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `held_bucket` / `held_180_600s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
