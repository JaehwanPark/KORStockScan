# Lifecycle Decision Matrix - 2026-05-22

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-22`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `35228`
- source_rows_total: `35228`
- retained_rows: `35228`
- dropped_rows_by_source: `{}`
- joined_rows: `33631`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `19`
- entry_bucket_runtime_candidate_count: `6`
- scale_in_bucket_actionable_count: `118`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1521 | 137 | 0.3471 | 1.0 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 129 | 123 | -0.2676 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 145 | 123 | -0.4473 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 32811 | 32785 | -0.159 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 622 | 463 | -0.428 | 1.0 | `pass` | `EXIT` | False |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1521, 'bucket_count': 139, 'actionable_bucket_count': 19, 'runtime_candidate_count': 6, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1297 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 218 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 1 | 0 | None | None | None | `hold_sample` |
| `chosen_action` | `WAIT_REQUOTE` | 4 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 88 | 36 | -0.128 | -0.6519 | 0.3889 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 24 | 24 | 2.1843 | 3.3856 | 0.875 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 168 | 20 | -0.7489 | -0.9905 | 0.3 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 71 | 11 | 0.263 | -0.7627 | 0.3636 | `hold_no_edge` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 21 | 9 | 0.1094 | -0.4356 | 0.5556 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 8 | 8 | 3.4799 | 5.9286 | 0.625 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 4 | 3 | -0.0865 | -0.17 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 19 | 3 | -1.3365 | -1.8367 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 3 | 3 | 0.3123 | 0.091 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 35 | 3 | -1.2521 | -0.4167 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 142 | 2 | -0.5602 | -0.76 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 11 | 2 | 0.0426 | -1.665 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 7 | 2 | -1.1512 | -0.74 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 124 | 2 | -1.9108 | -0.53 | 0.5 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 46 | 1 | -0.5192 | 1.55 | 1.0 | `hold_sample` |
| `exit_rule` | `exit_unknown` | 1419 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 34 | 34 | -0.3781 | 1.6615 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 29 | 29 | -0.2904 | -1.9386 | 0.0 | `hold_no_edge` |
| `exit_rule` | `scalp_hard_stop_pct` | 23 | 23 | -0.4198 | -2.9513 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1521 | 137 | 0.3471 | 0.4381 | 0.4891 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 1284 | 137 | 0.3471 | 0.4381 | 0.4891 | `candidate_recovery_or_relax` |
| `score_band` | `score_60_62` | 700 | 63 | -0.2895 | -0.6395 | 0.381 | `hold_no_edge` |
| `score_band` | `score_66_69` | 109 | 28 | 1.6584 | 2.8555 | 0.8214 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 640 | 27 | -0.2151 | -0.5867 | 0.4444 | `hold_no_edge` |
| `score_band` | `score_63_65` | 66 | 16 | 1.5141 | 2.2455 | 0.4375 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1065 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 35 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 700 | 80 | -0.3696 | -0.7194 | 0.3875 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 218 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_unknown` | 496 | 13 | -0.0714 | -0.7269 | 0.3846 | `hold_no_edge` |
| `strength_bucket` | `risk_unknown` | 1066 | 102 | -0.3299 | -0.6758 | 0.3922 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strength_unknown` | 218 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_0900_1000` | 330 | 63 | 0.0438 | -0.5683 | 0.4286 | `hold_no_edge` |
| `time_bucket` | `time_unknown` | 218 | 35 | 2.3199 | 3.6844 | 0.7714 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 418 | 33 | -0.8942 | -1.0012 | 0.2727 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_10`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_12`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_13`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_14`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_15`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_19`: `time_bucket` / `time_1000_1200` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `exit_rule` / `scalp_hard_stop_pct` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 32811, 'bucket_count': 3507, 'actionable_bucket_count': 118, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 14670, 'PYRAMID': 5034, 'arm_unknown': 13107}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 14221 | 14221 | -0.2243 | -0.2707 | 0.2823 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 7362 | 7362 | -0.1144 | -0.1347 | 0.2651 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 5688 | 5688 | -0.0983 | -0.1312 | 0.2322 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 4578 | 4578 | -0.1259 | -0.1554 | 0.209 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 936 | 936 | -0.0474 | -0.0755 | 0.1966 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 26 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 32811 | 32785 | -0.159 | -0.1943 | 0.2571 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 14670 | 14657 | -0.3673 | -0.4275 | 0.0 | `candidate_tighten_or_exclude` |
| `arm` | `arm_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `arm` | `PYRAMID` | 5034 | 5021 | 0.2457 | 0.1828 | 0.8196 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN` | 9973 | 9960 | -0.4206 | -0.4807 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 5034 | 5021 | 0.2457 | 0.1828 | 0.8196 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 4697 | 4697 | -0.2543 | -0.3147 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `blocker_reason_unknown` | 13107 | 13107 | -0.0811 | -0.0779 | 0.3291 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 3868 | 3868 | -0.1801 | -0.1904 | 0.12 | `hold_no_edge` |
| `blocker_reason` | `profit_not_enough` | 3633 | 3633 | 0.3993 | 0.3532 | 0.9408 | `candidate_recovery_or_relax` |
| `blocker_reason` | `near_market_close` | 1284 | 1284 | -0.073 | -0.073 | 0.1519 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.08)` | 1028 | 1028 | -0.0265 | -0.08 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.03)` | 555 | 555 | -0.027 | -0.03 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 532 | 532 | 0.0573 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 506 | 506 | -0.1376 | -0.1376 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `low_broken` | 402 | 402 | -0.3394 | -0.3636 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 339 | 339 | -0.0604 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.74)` | 335 | 335 | -0.6702 | -0.74 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.29)` | 286 | 286 | -1.184 | -1.29 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.76)` | 89 | 89 | -0.6967 | -0.76 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 87 | 87 | -0.0398 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 76 | 76 | -0.5846 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.96)` | 73 | 73 | -0.7814 | -0.96 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.82)` | 66 | 66 | -0.7168 | -0.82 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.12)` | 58 | 58 | -0.9965 | -1.12 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.28)` | 55 | 55 | -1.1711 | -1.28 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 47 | 47 | -0.6733 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.94)` | 47 | 47 | -0.8356 | -0.94 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.15)` | 46 | 46 | -1.094 | -1.15 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.24)` | 46 | 46 | -1.1417 | -1.24 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `ok` | 44 | 44 | -12.4279 | -15.5639 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-1.20)` | 44 | 44 | -1.0065 | -1.2 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.85)` | 41 | 41 | -0.8017 | -0.85 | 0.0 | `candidate_tighten_or_exclude` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `blocker_namespace` / `AVG_DOWN` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `blocker_reason` / `profit_not_enough` -> `candidate_recovery_or_relax`
- `scale_in_bucket_4`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `pnl_out_of_range(-0.74)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-1.29)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `candidate_tighten_or_exclude`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `blocker_namespace` / `AVG_DOWN` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_reason` / `profit_not_enough` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `pnl_out_of_range(-0.74)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-1.29)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-0.76)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(-0.96)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(-0.82)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

## Overnight Bucket Attribution

- decision_authority: `adm_ldm_overnight_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'overnight_rows': 60, 'bucket_count': 35, 'actionable_bucket_count': 0, 'runtime_candidate_count': 0, 'workorder_count': 0, 'status_counts': {'HOLD_OVERNIGHT': 20, 'SELL_TODAY': 40}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg010_pos080` | 12 | 12 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_neg070_neg010` | 5 | 5 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_lt_neg070` | 2 | 2 | -0.7612 | -1.015 | 0.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=SELL_TODAY|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | 3.34 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=action_unknown|status=SELL_TODAY|confidence=confidence_unknown|profit=profit_pos150_pos300_plus` | 1 | 1 | 2.505 | 3.34 | 1.0 | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_lt_neg070` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg010_pos080` | 12 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_neg070_neg010` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_overnight_decision` | `action=SELL_TODAY|status=HOLD_OVERNIGHT|confidence=confidence_070p|profit=profit_pos150_pos300_plus` | 1 | 0 | None | None | None | `hold_sample` |
| `confidence_band` | `confidence_070p` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `confidence_band` | `confidence_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `held_bucket` | `held_600_1800s_plus` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `held_bucket` | `held_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_action` | `SELL_TODAY` | 40 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_action` | `action_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_status` | `SELL_TODAY` | 40 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `overnight_status` | `HOLD_OVERNIGHT` | 20 | 0 | None | None | None | `hold_sample` |
| `peak_profit_band` | `peak_unknown` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `peak_profit_band` | `peak_lt_zero` | 28 | 14 | -0.2121 | -0.2829 | 0.0 | `hold_no_edge` |
| `peak_profit_band` | `peak_zero_pos080` | 10 | 5 | 0.201 | 0.268 | 1.0 | `hold_no_edge` |
| `price_source` | `holding_price_samples_last` | 60 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `profit_band` | `profit_neg010_pos080` | 36 | 24 | 0.0556 | 0.0742 | 0.4167 | `hold_no_edge` |
| `profit_band` | `profit_neg070_neg010` | 15 | 10 | -0.222 | -0.296 | 0.0 | `hold_no_edge` |
| `source_quality_gate` | `overnight_decision_coverage` | 60 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `source_stage` | `scalp_sim_overnight_sell_today` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `source_stage` | `scalp_sim_sell_order_assumed_filled` | 20 | 20 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |
| `stage` | `exit` | 40 | 40 | 0.027 | 0.036 | 0.3 | `hold_no_edge` |

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
