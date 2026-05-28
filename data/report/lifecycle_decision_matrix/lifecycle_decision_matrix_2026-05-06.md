# Lifecycle Decision Matrix - 2026-05-06

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-06`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `629`
- source_rows_total: `629`
- retained_rows: `629`
- dropped_rows_by_source: `{}`
- joined_rows: `596`
- policy_pass_count: `1`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `0`
- entry_bucket_runtime_candidate_count: `0`
- holding_bucket_count/workorders: `0` / `0`
- exit_bucket_count/workorders: `0` / `0`
- scale_in_bucket_actionable_count: `20`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_flow_bucket_count: `2`
- lifecycle_flow_complete_count: `0`
- lifecycle_flow_runtime_candidate_count: `0`
- identity_missing_count/join_rate: `0` / `1.0`
- complete_flow_rate: `0.0`
- incomplete_flow_reason_counts: `{'missing_entry': 18, 'missing_submit': 18, 'missing_holding': 18, 'missing_exit': 18}`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 629 | 596 | -2.9025 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

## Lifecycle Flow Bucket Attribution

- decision_authority: `adm_ldm_lifecycle_flow_bucket_attribution_source_only`
- metric_scope: `lifecycle_bundle_ev`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'flow_count': 18, 'complete_flow_count': 0, 'fallback_identity_count': 0, 'identity_missing_count': 0, 'identity_present_count': 629, 'identity_join_rate': 1.0, 'complete_flow_rate': 0.0, 'stage_identity': {'entry': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'submit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'holding': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}, 'scale_in': {'source_row_count': 629, 'identity_missing_count': 0, 'identity_quality_counts': {'candidate_id': 629}, 'identity_join_rate': 1.0}, 'exit': {'source_row_count': 0, 'identity_missing_count': 0, 'identity_quality_counts': {}, 'identity_join_rate': 0.0}}, 'incomplete_flow_reason_counts': {'missing_entry': 18, 'missing_submit': 18, 'missing_holding': 18, 'missing_exit': 18}, 'bucket_count': 2, 'runtime_candidate_count': 0, 'workorder_count': 18}`

| lifecycle_flow_bucket_id | sample | joined | ev | route | source_quality |
| --- | ---: | ---: | ---: | --- | --- |
| `lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holdin:8cd4f96ab3` | 17 | 6 | -0.3585 | `hold_sample` | `hold_sample_or_incomplete_flow` |
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
- summary: `{'scale_in_rows': 629, 'bucket_count': 147, 'actionable_bucket_count': 20, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 595, 'PYRAMID': 34}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 244 | 244 | -7.0653 | -8.8537 | 0.2377 | `candidate_tighten_or_exclude` |
| `ai_score_band` | `score_63_65` | 135 | 135 | -0.0386 | -0.0636 | 0.2963 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 92 | 92 | -0.0753 | -0.1077 | 0.2391 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 88 | 88 | 0.1091 | 0.0995 | 0.4091 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 37 | 37 | -0.0917 | -0.1149 | 0.2162 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 33 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 629 | 596 | -2.9025 | -3.6482 | 0.2752 | `candidate_tighten_or_exclude` |
| `arm` | `AVG_DOWN` | 595 | 584 | -1.6095 | -2.0319 | 0.2774 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 34 | 12 | -65.8275 | -82.3058 | 0.1667 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 541 | 541 | -1.7159 | -2.1718 | 0.2994 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 43 | 43 | -0.2714 | -0.2714 | 0.0 | `hold_no_edge` |
| `blocker_namespace` | `PYRAMID` | 12 | 12 | -65.8275 | -82.3058 | 0.1667 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PRICE_GUARD` | 22 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 11 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `scale_in_gate_blocked` | 141 | 141 | -0.0892 | -0.185 | 0.1631 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 107 | 107 | -0.2055 | -0.2055 | 0.1215 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 84 | 84 | 0.1462 | 0.0564 | 0.5476 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 37 | 37 | -0.2943 | -0.2943 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `scale_in_cooldown` | 28 | 28 | -0.0393 | -0.0393 | 0.4286 | `hold_no_edge` |
| `blocker_reason` | `🛑 하드스탑 도달 (-2.5%) [AI: 50]` | 27 | 27 | -52.9882 | -66.1778 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.78)` | 12 | 12 | 0.78 | 0.78 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 11 | 11 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `ai_not_recovering` | 9 | 9 | -0.3556 | -0.3556 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.11)` | 9 | 9 | 0.11 | 0.11 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.60)` | 5 | 5 | 0.6 | 0.6 | 1.0 | `candidate_recovery_or_relax` |
| `held_bucket` | `held_600_1800s` | 221 | 221 | -0.0492 | -0.0833 | 0.2986 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 155 | 155 | -0.0232 | -0.1329 | 0.5161 | `hold_no_edge` |
| `held_bucket` | `held_180_600s` | 135 | 135 | -0.2109 | -0.2379 | 0.0889 | `hold_no_edge` |
| `held_bucket` | `held_020_180s` | 48 | 48 | -0.3455 | -0.3615 | 0.125 | `candidate_tighten_or_exclude` |
| `held_bucket` | `held_lt020s` | 37 | 37 | -45.1449 | -56.3732 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_unknown` | 357 | 324 | -0.0916 | -0.0916 | 0.287 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 141 | 141 | -0.0615 | -0.154 | 0.2979 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 91 | 91 | -18.8258 | -23.4888 | 0.0 | `candidate_tighten_or_exclude` |
| `peak_profit_band` | `peak_pos080_pos150` | 38 | 38 | 0.4812 | 0.2955 | 0.7105 | `candidate_recovery_or_relax` |
| `price_guard_reason` | `price_guard_none` | 607 | 596 | -2.9025 | -3.6482 | 0.2752 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_neg070_neg010` | 265 | 265 | -0.2715 | -0.31 | 0.0 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 236 | 236 | 0.2121 | 0.1819 | 0.6144 | `hold_no_edge` |
| `profit_band` | `profit_lt_neg070` | 76 | 76 | -22.7686 | -28.3871 | 0.0 | `candidate_tighten_or_exclude` |
| `profit_band` | `profit_pos080_pos150` | 17 | 17 | 1.1226 | 1.1188 | 1.0 | `candidate_recovery_or_relax` |
| `qty_reason` | `qty_none` | 618 | 596 | -2.9025 | -3.6482 | 0.2752 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `ai_score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `arm` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_namespace` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `🛑 하드스탑 도달 (-2.5%) [AI: 50]` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(0.78)` -> `candidate_recovery_or_relax`
- `scale_in_bucket_11`: `held_bucket` / `held_020_180s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_12`: `held_bucket` / `held_lt020s` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_13`: `peak_profit_band` / `peak_lt_zero` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `ai_score_band` / `score_lt60` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `ai_score_source` / `ai_source_unknown` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `🛑 하드스탑 도달 (-2.5%) [AI: 50]` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(0.78)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `ai_not_recovering` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(0.60)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
