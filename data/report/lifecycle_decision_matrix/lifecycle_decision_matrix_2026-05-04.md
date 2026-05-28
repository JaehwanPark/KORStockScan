# Lifecycle Decision Matrix - 2026-05-04

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-04`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `3517`
- source_rows_total: `3517`
- retained_rows: `3517`
- dropped_rows_by_source: `{}`
- joined_rows: `3517`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `0` / `0`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `77`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `2`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 39, 'missing_submit': 39, 'missing_holding': 39, 'missing_exit': 39}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 3517 | 3517 | -0.7281 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 39, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 3517, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'holding': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'scale_in': {'source_row_count': 3517, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 3517}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 39, 'missing_submit': 39, 'missing_holding': 39, 'missing_exit': 39}, 'bucket_count': 2, 'runtime_candidate_count': 0, 'workorder_count': 20}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 37 | 37 | -0.1174 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2 | 2 | -26.526 | `hold_sample` | `hold_sample_or_incomplete_flow` |

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
- summary: `{'scale_in_rows': 3517, 'bucket_count': 675, 'actionable_bucket_count': 77, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 3453, 'PYRAMID': 64}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 2527 | 2527 | -1.0315 | -1.2535 | 0.1939 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 355 | 355 | -0.152 | -0.1933 | 0.2479 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 253 | 253 | -0.0068 | -0.0402 | 0.3123 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 210 | 210 | 0.4985 | 0.4849 | 0.819 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 172 | 172 | -0.0174 | -0.0519 | 0.4244 | `hold_no_edge` |
| `ai_score_source` | `ai_source_unknown` | 3517 | 3517 | -0.7281 | -0.8966 | 0.2565 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 3453 | 3453 | -0.5449 | -0.6594 | 0.2456 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 64 | 64 | -10.6105 | -13.6966 | 0.8438 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 3010 | 3010 | -0.565 | -0.6963 | 0.2817 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 443 | 443 | -0.4084 | -0.4084 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 64 | 64 | -10.6105 | -13.6966 | 0.8438 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_probe_blocked` | 946 | 946 | -0.1568 | -0.281 | 0.3541 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 607 | 607 | -0.3377 | -0.3377 | 0.0873 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_gate_blocked` | 370 | 370 | -0.228 | -0.3337 | 0.0892 | `hold_no_edge` |
| `blocker_reason` | `🔪 소프트 손절 (-1.5%) [AI: 50]` | 62 | 62 | -1.6477 | -1.654 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 54 | 54 | 2.1146 | 2.1189 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `🔪 소프트 손절 (-1.5%) [AI: 48]` | 52 | 52 | -1.366 | -1.65 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.05)` | 42 | 42 | 0.05 | 0.05 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 30 | 30 | -55.622 | -69.47 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.02)` | 23 | 23 | -0.02 | -0.02 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.92)` | 22 | 22 | -0.92 | -0.92 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.27)` | 22 | 22 | 0.27 | 0.27 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `scale_in_cooldown` | 22 | 22 | -0.3491 | -0.3491 | 0.1364 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 21 | 21 | -0.08 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.07)` | 19 | 19 | -1.07 | -1.07 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.40)` | 17 | 17 | 0.4 | 0.4 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 16 | 16 | -0.71 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.11)` | 16 | 16 | -1.11 | -1.11 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.01)` | 15 | 15 | 0.01 | 0.01 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.11)` | 14 | 14 | 0.11 | 0.11 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.48)` | 14 | 14 | 0.48 | 0.48 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.83)` | 13 | 13 | -0.83 | -0.83 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.13)` | 13 | 13 | 0.13 | 0.13 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.32)` | 13 | 13 | 0.32 | 0.32 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(1.30)` | 13 | 13 | 1.3 | 1.3 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 11 | 11 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 11 | 11 | -0.74 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 11 | 11 | -0.89 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.00)` | 11 | 11 | -1.0 | -1.0 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.50)` | 11 | 11 | 0.5 | 0.5 | 1.0 | `candidate_recovery_or_relax` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `scale_in_bucket_4`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `arm` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_namespace` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `add_judgment_locked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `🔪 소프트 손절 (-1.5%) [AI: 50]` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_reason` / `scalping_pyramid_ok` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `add_judgment_locked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `🔪 소프트 손절 (-1.5%) [AI: 50]` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
