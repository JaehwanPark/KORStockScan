# Lifecycle Decision Matrix - 2026-05-08

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-08`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `62`
- source_rows_total: `62`
- retained_rows: `62`
- dropped_rows_by_source: `{}`
- joined_rows: `47`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `0` / `0`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `23`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `2`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 8, 'missing_submit': 8, 'missing_holding': 8, 'missing_exit': 8}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 62 | 47 | -14.3711 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 8, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 62, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'holding': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'scale_in': {'source_row_count': 62, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 62}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 8, 'missing_submit': 8, 'missing_holding': 8, 'missing_exit': 8}, 'bucket_count': 2, 'runtime_candidate_count': 0, 'workorder_count': 8}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 7 | 3 | -0.0522 | `hold_sample` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'scale_in_rows': 62, 'bucket_count': 67, 'actionable_bucket_count': 23, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 44, 'PYRAMID': 18}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 17 | 17 | -39.5842 | -49.4488 | 0.0 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_70p` | 16 | 16 | 0.3961 | 0.38 | 0.5625 | `candidate_recovery_or_relax` |
| `ai_score_band` | `score_66_69` | 8 | 8 | -0.5485 | -0.635 | 0.125 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_60_62` | 3 | 3 | 0.2467 | 0.2467 | 0.6667 | `hold_sample` |
| `ai_score_band` | `score_63_65` | 3 | 3 | -1.734 | -1.99 | 0.0 | `hold_sample` |
| `ai_score_band` | `score_unknown` | 15 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 62 | 47 | -14.3711 | -17.9757 | 0.2553 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 44 | 40 | -9.0923 | -11.348 | 0.225 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 18 | 7 | -44.536 | -55.8486 | 0.4286 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 37 | 37 | -9.8106 | -12.2492 | 0.2432 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 7 | 7 | -44.536 | -55.8486 | 0.4286 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 3 | 3 | -0.2333 | -0.2333 | 0.0 | `hold_sample` |
| `blocker_namespace` | `PRICE_GUARD` | 11 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 4 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 11 | 11 | -53.4671 | -66.7764 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `scale_in_probe_blocked` | 10 | 10 | -0.335 | -0.508 | 0.3 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `add_judgment_locked` | 3 | 3 | -0.0633 | -0.0633 | 0.3333 | `hold_sample` |
| `blocker_reason` | `scalping_pyramid_ok` | 3 | 3 | 1.8507 | 1.82 | 1.0 | `hold_sample` |
| `blocker_reason` | `pnl_out_of_range(-1.16)` | 2 | 2 | -1.16 | -1.16 | 0.0 | `hold_sample` |
| `blocker_reason` | `scale_in_gate_blocked` | 2 | 2 | -0.401 | -0.625 | 0.0 | `hold_sample` |
| `held_bucket` | `held_020_180s` | 19 | 19 | 0.3131 | 0.2816 | 0.6316 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_lt020s` | 16 | 16 | -41.7602 | -52.1462 | 0.0 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_180_600s` | 12 | 12 | -1.1023 | -1.3225 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_lt_zero` | 19 | 19 | -35.42 | -44.2295 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 33 | 18 | -0.3606 | -0.3606 | 0.3333 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 6 | 6 | -0.2743 | -0.5983 | 0.3333 | `hold_no_edge` |
| `price_guard_reason` | `price_guard_none` | 51 | 47 | -14.3711 | -17.9757 | 0.2553 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_lt_neg070` | 26 | 26 | -26.2844 | -32.7769 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 9 | 9 | -0.3447 | -0.3944 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg010_pos080` | 6 | 6 | 0.4233 | 0.4117 | 1.0 | `candidate_recovery_or_relax` |
| `qty_reason` | `qty_none` | 58 | 47 | -14.3711 | -17.9757 | 0.2553 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_unknown` | 44 | 29 | -23.0674 | -28.9093 | 0.2069 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_1` | 6 | 6 | -1.055 | -1.055 | 0.0 | `candidate_tighten_or_exclude` |
| `supply_pass_bucket` | `supply_pass_2` | 6 | 6 | 0.03 | 0.03 | 0.5 | `hold_no_edge` |
| `time_bucket` | `time_unknown` | 62 | 47 | -14.3711 | -17.9757 | 0.2553 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `ai_score_band` / `score_70p` -> `candidate_recovery_or_relax`
- `scale_in_bucket_5`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `🛑 하드스탑 도달 (-2.5%) [AI: 50]` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `scale_in_probe_blocked` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_11`: `held_bucket` / `held_020_180s` -> `candidate_recovery_or_relax`
- `scale_in_bucket_12`: `held_bucket` / `held_lt020s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_13`: `held_bucket` / `held_180_600s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_14`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_band` / `score_70p` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `ai_score_band` / `score_66_69` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `🛑 하드스탑 도달 (-2.5%) [AI: 50]` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `scale_in_probe_blocked` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
