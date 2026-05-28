# Lifecycle Decision Matrix - 2026-05-02

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-02`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `6`
- source_rows_total: `6`
- retained_rows: `6`
- dropped_rows_by_source: `{}`
- joined_rows: `6`
- policy_pass_count: `0`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `0` / `0`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `10`
- scale_in_bucket_runtime_candidate_count: `0`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `1`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 1, 'missing_submit': 1, 'missing_holding': 1, 'missing_exit': 1}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `['all_stage_policy_entries_below_sample_floor']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 6 | 6 | -55.622 | 0.6 | `hold_sample` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 1, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 6, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'holding': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'scale_in': {'source_row_count': 6, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 6}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 1, 'missing_submit': 1, 'missing_holding': 1, 'missing_exit': 1}, 'bucket_count': 1, 'runtime_candidate_count': 0, 'workorder_count': 1}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 1 | 1 | -55.622 | `hold_sample` | `hold_sample_or_incomplete_flow` |

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
- summary: `{'submit_rows': 0, 'bucket_count': 0, 'contract_gap_count': 0, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |

### Submit Bucket Workorders

- none

## Holding Bucket Attribution

- decision_authority: `adm_ldm_holding_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- allowed_runtime_apply: `False`
- summary: `{'holding_rows': 0, 'source_row_count': 0, 'bucket_count': 0, 'joined_sample': 0, 'source_quality_adjusted_ev_pct': None, 'source_quality_gate': 'hold_sample', 'unknown_reason_counts': {}, 'workorder_count': 0, 'runtime_candidate_count': 0}`

| bucket_type | bucket_key | sample | joined | ev | route |
| --- | --- | ---: | ---: | ---: | --- |

### Holding Bucket Attribution Workorders

- none

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
- summary: `{'scale_in_rows': 6, 'bucket_count': 14, 'actionable_bucket_count': 10, 'runtime_candidate_count': 0, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 2, 'AVG_DOWN': 4}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_source` | `ai_source_unknown` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 4 | 4 | -43.77 | -54.655 | 0.0 | `hold_sample` |
| `arm` | `PYRAMID` | 2 | 2 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_namespace` | `AVG_DOWN` | 4 | 4 | -43.77 | -54.655 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PYRAMID` | 2 | 2 | -79.326 | -99.1 | 0.0 | `hold_sample` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_lt020s` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `price_guard_reason` | `price_guard_none` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `qty_reason` | `qty_none` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_unknown` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `time_bucket` | `time_unknown` | 6 | 6 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- none

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_reason` / `🛑 하드스탑 도달 (-2.5%) [AI: 50]` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `held_bucket` / `held_lt020s` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `peak_profit_band` / `peak_lt_zero` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `price_guard_reason` / `price_guard_none` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `profit_band` / `profit_lt_neg070` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `qty_reason` / `qty_none` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `supply_pass_bucket` / `supply_pass_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `time_bucket` / `time_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
