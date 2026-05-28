# Lifecycle Decision Matrix - 2026-05-13

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-13`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `351`
- source_rows_total: `351`
- retained_rows: `351`
- dropped_rows_by_source: `{}`
- joined_rows: `234`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `5` / `4`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `3`
- scale_in_bucket_runtime_candidate_count: `3`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `2`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 237, 'missing_exit': 237, 'missing_submit': 236, 'missing_holding': 236}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 1 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 1 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 349 | 234 | -0.1725 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 237, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 351, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'holding': {'source_row_count': 1, 'identity_missing_count': 0, 'identity_quality_counts': {'exact_sim_record_id': 1}, 'identity_join_rate': 1.0}, 'scale_in': {'source_row_count': 349, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 349}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 237, 'missing_exit': 237, 'missing_submit': 236, 'missing_holding': 236}, 'bucket_count': 2, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 236 | 234 | -0.1725 | `hold_sample` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'submit_rows': 1, 'bucket_count': 15, 'contract_gap_count': 2, 'workorder_count': 2, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `actual_order_submitted` | `false` | 1 | 0 | None | `keep_collecting` |
| `broker_order_forbidden` | `broker_order_forbidden_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `combo_submit_quality` | `source=scalp_sim_buy_order_assumed_filled|revalidation=ok_or_unflagged|quote_age=quote_age_unknown|liquidity=liquidity_unknown|liquidity_guard=liquidity_guard_unknown|overbought=overbought_unknown|latency=latency_unknown|fill=false|submitted=false` | 1 | 0 | None | `source_quality_workorder` |
| `latency_reason` | `latency_reason_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `latency_state` | `latency_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_bucket` | `liquidity_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `liquidity_guard_action` | `liquidity_guard_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `overbought_bucket` | `overbought_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `overbought_guard_action` | `overbought_guard_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `price_below_bid_bucket` | `price_below_bid_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `price_resolution_bucket` | `price_resolution_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `quote_age_bucket` | `quote_age_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `revalidation_state` | `ok_or_unflagged` | 1 | 0 | None | `keep_collecting` |
| `submit_source_stage` | `scalp_sim_buy_order_assumed_filled` | 1 | 0 | None | `keep_collecting` |
| `would_limit_fill` | `false` | 1 | 0 | None | `keep_collecting` |

### Submit Bucket Workorders

- `order_entry_post_submit_contract_gap_review`: `post_submit_contract_gap` / `price_revalidation_or_submit_state_missing` -> `price_revalidation_or_submit_state_missing`
- `order_entry_sim_submit_path_bucket_instrumentation`: `sim_pre_submit_guard_contract_gap` / `sim_pre_submit_guard_bucket_fields_missing` -> `sim_pre_submit_guard_bucket_fields_missing`

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 1, 'source_row_count': 1, 'bucket_count': 5, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {'join_gap': 6}, 'workorder_count': 4, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |
| `combo_holding_flow` | `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `held_bucket` | `held_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `holding_action` | `holding_action_unknown` | 1 | 0 | None | `source_quality_workorder` |
| `holding_source_stage` | `scalp_sim_holding_started` | 1 | 0 | None | `hold_sample` |
| `profit_band` | `profit_unknown` | 1 | 0 | None | `source_quality_workorder` |

### Holding Bucket Attribution Workorders

- `holding_bucket_source_quality_1`: `combo_holding_flow` / `source=scalp_sim_holding_started|action=holding_action_unknown|profit=profit_unknown|held=held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_2`: `held_bucket` / `held_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_3`: `holding_action` / `holding_action_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`
- `holding_bucket_source_quality_4`: `profit_band` / `profit_unknown` -> `holding_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`

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
- summary: `{'scale_in_rows': 349, 'bucket_count': 84, 'actionable_bucket_count': 3, 'runtime_candidate_count': 3, 'workorder_count': 3, 'arm_counts': {'AVG_DOWN': 334, 'PYRAMID': 15}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_70p` | 234 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 115 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 349 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 334 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |
| `arm` | `PYRAMID` | 15 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 188 | 188 | -0.1518 | -0.1675 | 0.2979 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 46 | 46 | -0.2574 | -0.2574 | 0.0 | `hold_no_edge` |
| `blocker_namespace` | `QTY_GUARD` | 115 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `add_judgment_locked` | 84 | 84 | -0.1832 | -0.1832 | 0.2381 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 74 | 74 | -0.1445 | -0.1804 | 0.2297 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 11 | 11 | -0.1567 | -0.1845 | 0.3636 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.02)` | 9 | 9 | 0.02 | 0.02 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.15)` | 6 | 6 | 0.15 | 0.15 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `ai_not_recovering` | 3 | 3 | -0.44 | -0.44 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1005s)` | 1 | 1 | -0.36 | -0.36 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1045s)` | 1 | 1 | -0.36 | -0.36 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1088s)` | 1 | 1 | -0.1 | -0.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1129s)` | 1 | 1 | -0.23 | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1173s)` | 1 | 1 | -0.23 | -0.23 | 0.0 | `hold_sample` |
| `blocker_reason` | `hold_sec_out_of_range(1214s)` | 1 | 1 | -0.36 | -0.36 | 0.0 | `hold_sample` |
| `held_bucket` | `held_600_1800s` | 105 | 105 | -0.1953 | -0.2071 | 0.1238 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 77 | 77 | -0.0117 | -0.0245 | 0.5584 | `hold_no_edge` |
| `held_bucket` | `held_180_600s` | 38 | 38 | -0.3305 | -0.3437 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 12 | 12 | -0.4757 | -0.4925 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 264 | 149 | -0.1876 | -0.1876 | 0.2349 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 45 | 45 | -0.2712 | -0.306 | 0.0 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 40 | 40 | -0.0055 | -0.0403 | 0.525 | `hold_no_edge` |
| `price_guard_reason` | `price_guard_none` | 349 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 123 | 123 | -0.3171 | -0.3336 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 111 | 111 | -0.0123 | -0.0207 | 0.5045 | `hold_no_edge` |
| `qty_reason` | `qty_none` | 234 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_unknown` | 200 | 85 | -0.1461 | -0.1809 | 0.2471 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_2` | 48 | 48 | -0.2058 | -0.2058 | 0.1667 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_3` | 41 | 41 | -0.1112 | -0.1112 | 0.3171 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_1` | 26 | 26 | -0.2935 | -0.2935 | 0.1154 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_0` | 18 | 18 | -0.0833 | -0.0833 | 0.6111 | `hold_no_edge` |
| `supply_pass_bucket` | `supply_pass_3_plus` | 16 | 16 | -0.2737 | -0.2737 | 0.0 | `hold_no_edge` |
| `time_bucket` | `time_unknown` | 349 | 234 | -0.1725 | -0.1852 | 0.2393 | `hold_no_edge` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `held_bucket` / `held_180_600s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `held_bucket` / `held_020_180s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `profit_band` / `profit_neg070_neg010` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `held_bucket` / `held_180_600s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `held_bucket` / `held_020_180s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `profit_band` / `profit_neg070_neg010` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
