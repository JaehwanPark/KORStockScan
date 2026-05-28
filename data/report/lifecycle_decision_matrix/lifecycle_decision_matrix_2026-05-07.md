# Lifecycle Decision Matrix - 2026-05-07

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-07`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `469`
- source_rows_total: `469`
- retained_rows: `469`
- dropped_rows_by_source: `{}`
- joined_rows: `457`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `0` / `0`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `40`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `2`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 11, 'missing_submit': 11, 'missing_holding': 11, 'missing_exit': 11}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 469 | 457 | -0.8488 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 11, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 469, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'holding': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'scale_in': {'source_row_count': 469, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 469}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 11, 'missing_submit': 11, 'missing_holding': 11, 'missing_exit': 11}, 'bucket_count': 2, 'runtime_candidate_count': 0, 'workorder_count': 11}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 9 | 8 | -0.589 | `hold_sample` | `hold_sample_or_incomplete_flow` |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:7d607fe77a` | 2 | 2 | -26.8825 | `hold_sample` | `hold_sample_or_incomplete_flow` |

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
- summary: `{'scale_in_rows': 469, 'bucket_count': 168, 'actionable_bucket_count': 40, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'PYRAMID': 21, 'AVG_DOWN': 448}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 205 | 205 | -1.5542 | -1.9043 | 0.0488 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 87 | 87 | 0.0783 | 0.0615 | 0.2874 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 68 | 68 | -0.5628 | -0.6684 | 0.0441 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 60 | 60 | -0.3838 | -0.4292 | 0.15 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_66_69` | 37 | 37 | -0.4006 | -0.4473 | 0.1081 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_unknown` | 12 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 469 | 457 | -0.8488 | -1.0346 | 0.1116 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 448 | 447 | -0.733 | -0.8781 | 0.094 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 21 | 10 | -6.026 | -8.03 | 0.9 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 405 | 405 | -0.7649 | -0.925 | 0.1037 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 42 | 42 | -0.4255 | -0.4255 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 10 | 10 | -6.026 | -8.03 | 0.9 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PRICE_GUARD` | 6 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 6 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `scale_in_probe_blocked` | 110 | 110 | -0.6077 | -0.8439 | 0.0818 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 92 | 92 | -0.457 | -0.457 | 0.0652 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_gate_blocked` | 59 | 59 | -0.1813 | -0.4271 | 0.0508 | `hold_no_edge` |
| `blocker_reason` | `ai_not_recovering` | 13 | 13 | -0.3946 | -0.3946 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.98)` | 13 | 13 | -0.98 | -0.98 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.83)` | 10 | 10 | -0.83 | -0.83 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scalping_pyramid_ok` | 9 | 9 | 2.1184 | 2.0889 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 5 | 5 | -0.95 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.24)` | 5 | 5 | -1.24 | -1.24 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.44)` | 5 | 5 | -1.44 | -1.44 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s` | 161 | 161 | -0.4262 | -0.5488 | 0.1491 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 151 | 151 | -0.7674 | -0.8595 | 0.0596 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_020_180s` | 97 | 97 | -0.3865 | -0.4236 | 0.0928 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_600_1800s_plus` | 35 | 35 | 0.0887 | -0.084 | 0.2571 | `hold_no_edge` |
| `held_bucket` | `held_lt020s` | 13 | 13 | -13.0037 | -16.2008 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 282 | 270 | -0.5694 | -0.5694 | 0.1111 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_zero_pos080` | 97 | 97 | -0.6401 | -0.8428 | 0.0722 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 44 | 44 | -4.3544 | -5.4059 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos150_pos300` | 44 | 44 | 0.3959 | -0.0341 | 0.2727 | `candidate_recovery_or_relax` |
| `price_guard_reason` | `price_guard_none` | 463 | 457 | -0.8488 | -1.0346 | 0.1116 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 197 | 197 | -1.8332 | -2.1753 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 196 | 196 | -0.3435 | -0.4254 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 46 | 46 | 0.1985 | 0.1737 | 0.7174 | `hold_no_edge` |
| `profit_band` | `profit_pos150_pos300` | 12 | 12 | 2.1122 | 2.09 | 1.0 | `candidate_recovery_or_relax` |
| `profit_band` | `profit_pos080_pos150` | 6 | 6 | 1.0133 | 1.0083 | 1.0 | `candidate_recovery_or_relax` |
| `qty_reason` | `qty_none` | 463 | 457 | -0.8488 | -1.0346 | 0.1116 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `ai_score_band` / `score_63_65` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `ai_score_band` / `score_66_69` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `arm` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_namespace` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `blocker_reason` / `scale_in_probe_blocked` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_60_62` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_63_65` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
