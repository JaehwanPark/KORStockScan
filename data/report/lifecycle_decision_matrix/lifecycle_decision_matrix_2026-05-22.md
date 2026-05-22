# Lifecycle Decision Matrix - 2026-05-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-22`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `9863`
- source_rows_total: `9863`
- retained_rows: `9863`
- dropped_rows_by_source: `{}`
- joined_rows: `9641`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `8`
- entry_bucket_runtime_candidate_count: `0`
- scale_in_bucket_actionable_count: `91`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 100 | 16 | 3.4568 | 0.256 | `pass` | `BUY_DEFENSIVE` | False |
| `submit` | 89 | 75 | -0.6286 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 89 | 75 | -0.6204 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 9296 | 9289 | -0.142 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 289 | 186 | -0.4256 | 1.0 | `pass` | `EXIT` | False |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 100, 'bucket_count': 24, 'actionable_bucket_count': 8, 'runtime_candidate_count': 0, 'workorder_count': 8}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `action_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 9 | 9 | 2.7786 | 4.9087 | 0.8889 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 5 | 5 | 6.5153 | 10.874 | 0.8 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 2 | 2 | -1.137 | -0.5042 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_bottoming_entry_allowed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 6 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 51 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_bottoming_entry_allowed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 7 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 14 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 14 | 9 | 2.7786 | 4.9087 | 0.8889 | `hold_sample` |
| `score_band` | `score_63_65` | 13 | 5 | 6.5153 | 10.874 | 0.8 | `hold_sample` |
| `score_band` | `score_70p` | 2 | 2 | -1.137 | -0.5042 | 0.5 | `hold_sample` |
| `score_band` | `score_60_62` | 57 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_lt60` | 14 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 16 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_sim_panic_bottoming_entry_allowed` | 7 | 0 | None | None | None | `hold_sample` |
| `stale_bucket` | `fresh_or_unflagged` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strength_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_unknown` | 100 | 16 | 3.4568 | 6.0962 | 0.8125 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- none

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `strength_bucket` / `strength_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `time_bucket` / `time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 9296, 'bucket_count': 885, 'actionable_bucket_count': 91, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 3312, 'PYRAMID': 1561, 'arm_unknown': 4423}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 3554 | 3554 | -0.1213 | -0.1629 | 0.3571 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 2399 | 2399 | -0.1801 | -0.2148 | 0.3243 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 1716 | 1716 | -0.0887 | -0.1362 | 0.4021 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 1385 | 1385 | -0.1991 | -0.2463 | 0.2996 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 235 | 235 | -0.1191 | -0.1841 | 0.4809 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 7 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 9296 | 9289 | -0.142 | -0.1843 | 0.3515 | `hold_no_edge` |
| `arm` | `arm_unknown` | 4423 | 4423 | -0.0833 | -0.0783 | 0.3941 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 3312 | 3306 | -0.5472 | -0.6412 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `PYRAMID` | 1561 | 1560 | 0.5504 | 0.4832 | 0.9756 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `blocker_namespace_unknown` | 4423 | 4423 | -0.0833 | -0.0783 | 0.3941 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN` | 2147 | 2141 | -0.6893 | -0.7857 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 1561 | 1560 | 0.5504 | 0.4832 | 0.9756 | `candidate_recovery_or_relax` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 1165 | 1165 | -0.2861 | -0.3756 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 4423 | 4423 | -0.0833 | -0.0783 | 0.3941 | `hold_no_edge` |
| `blocker_reason` | `profit_not_enough` | 1324 | 1324 | 0.525 | 0.4589 | 0.9728 | `candidate_recovery_or_relax` |
| `blocker_reason` | `add_judgment_locked` | 763 | 763 | -0.2267 | -0.2609 | 0.2647 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 234 | 234 | -0.3345 | -0.364 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 52 | 52 | -0.7169 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 51 | 51 | -0.7881 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 46 | 46 | -0.6882 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 42 | 42 | 0.0053 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.90)` | 38 | 38 | -0.7983 | -0.9 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.12)` | 38 | 38 | -0.9804 | -1.12 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 32 | 32 | -1.0006 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `trend_not_strong` | 31 | 31 | 3.0538 | 3.1248 | 1.0 | `candidate_recovery_or_relax` |
| `blocker_reason` | `ok` | 30 | 30 | -1.8321 | -2.3747 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 30 | 30 | -0.589 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 29 | 29 | -0.8162 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.02)` | 27 | 27 | 0.033 | -0.02 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 27 | 27 | -0.0355 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-1.28)` | 25 | 25 | -1.1291 | -1.28 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 24 | 24 | -0.6644 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.24)` | 24 | 24 | -1.1078 | -1.24 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.41)` | 24 | 24 | -1.2829 | -1.41 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 22 | 22 | -0.609 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.75)` | 21 | 21 | -0.581 | -0.75 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.89)` | 20 | 20 | -0.8031 | -0.89 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.38)` | 20 | 20 | -1.1854 | -1.38 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 19 | 19 | -0.0064 | -0.03 | 0.0 | `hold_no_edge` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `arm` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_3`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_namespace` / `PYRAMID` -> `candidate_recovery_or_relax`
- `scale_in_bucket_5`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_6`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(-0.90)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(-0.90)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
