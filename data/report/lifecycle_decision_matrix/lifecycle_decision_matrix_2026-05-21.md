# Lifecycle Decision Matrix - 2026-05-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-21`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `40910`
- source_rows_total: `40910`
- retained_rows: `40910`
- dropped_rows_by_source: `{}`
- joined_rows: `39149`
- policy_pass_count: `5`
- promote_ready_count: `0`
- entry_bucket_actionable_count: `28`
- entry_bucket_runtime_candidate_count: `10`
- scale_in_bucket_actionable_count: `207`
- scale_in_bucket_runtime_candidate_count: `10`
- overnight_bucket_actionable_count: `0`
- overnight_bucket_runtime_candidate_count: `0`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 1, 'route_counts': {'bounded_auxiliary_weight': 1, 'hold_sample': 4}, 'quality_counts': {'observational_only_pending_outcome': 1, 'hold_sample': 4}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1671 | 232 | -0.2995 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 196 | 180 | -1.011 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 189 | 180 | -0.6538 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 37853 | 37788 | -0.1504 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 1001 | 769 | -0.5019 | 1.0 | `pass` | `EXIT` | False |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 1671, 'bucket_count': 135, 'actionable_bucket_count': 28, 'runtime_candidate_count': 10, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `NO_BUY_AI` | 1440 | 174 | -0.9845 | -0.2668 | 0.4023 | `candidate_tighten_or_exclude` |
| `chosen_action` | `action_unknown` | 228 | 57 | 1.8946 | 3.7223 | 0.614 | `candidate_recovery_or_relax` |
| `chosen_action` | `SKIP_PRE_SUBMIT_SAFETY` | 1 | 1 | -6.1601 | 5.57 | 1.0 | `hold_sample` |
| `chosen_action` | `SKIP_SOURCE_QUALITY` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 187 | 46 | -1.4571 | -0.1248 | 0.413 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 44 | 44 | 1.7691 | 3.5748 | 0.6591 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 94 | 39 | -0.4221 | -0.0244 | 0.4615 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 75 | 12 | -0.718 | -0.5292 | 0.5 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 143 | 11 | -1.2279 | 0.2355 | 0.4545 | `candidate_tighten_or_exclude` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 9 | 9 | 2.483 | 4.5894 | 0.5556 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 153 | 8 | -1.4624 | -0.9825 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=stale_block|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 15 | 6 | -1.3409 | -1.285 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 10 | 6 | 0.0235 | -0.9067 | 0.3333 | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 203 | 5 | -1.7949 | -0.6 | 0.4 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 21 | 4 | -0.1213 | -0.7575 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` | 5 | 4 | -1.9528 | -0.6625 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 4 | 4 | 1.9506 | 3.393 | 0.25 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1400_close` | 43 | 3 | 0.2646 | -0.34 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` | 7 | 3 | -1.8733 | 1.7867 | 0.6667 | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1200_1400` | 18 | 3 | -2.1678 | 0.56 | 0.6667 | `hold_sample` |
| `exit_rule` | `scalp_sim_panic_lifecycle_full_exit` | 60 | 60 | -0.5081 | -0.2718 | 0.25 | `candidate_tighten_or_exclude` |
| `exit_rule` | `exit_unknown` | 1496 | 57 | 1.8946 | 3.7223 | 0.614 | `candidate_recovery_or_relax` |
| `exit_rule` | `scalp_trailing_take_profit` | 50 | 50 | -1.4996 | 1.6334 | 1.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_soft_stop_pct` | 38 | 38 | -1.3468 | -1.855 | 0.0 | `candidate_tighten_or_exclude` |
| `exit_rule` | `scalp_hard_stop_pct` | 15 | 15 | -0.6959 | -2.7427 | 0.0 | `candidate_tighten_or_exclude` |
| `liquidity_bucket` | `liquidity_unknown` | 1671 | 232 | -0.2995 | 0.7384 | 0.4569 | `hold_no_edge` |
| `overbought_bucket` | `overbought_unknown` | 1444 | 232 | -0.2995 | 0.7384 | 0.4569 | `hold_no_edge` |
| `score_band` | `score_60_62` | 789 | 107 | -1.0297 | -0.2935 | 0.3925 | `candidate_tighten_or_exclude` |
| `score_band` | `score_66_69` | 86 | 55 | 1.2805 | 2.8437 | 0.6182 | `candidate_recovery_or_relax` |
| `score_band` | `score_lt60` | 698 | 44 | -0.8706 | -0.39 | 0.4318 | `candidate_tighten_or_exclude` |
| `score_band` | `score_63_65` | 91 | 21 | 0.3306 | 2.1107 | 0.4286 | `candidate_recovery_or_relax` |
| `source_stage` | `scalp_entry_action_decision_snapshot` | 1215 | 174 | -0.9845 | -0.2668 | 0.4023 | `candidate_tighten_or_exclude` |
| `source_stage` | `wait6579_ev_cohort` | 57 | 57 | 1.8946 | 3.7223 | 0.614 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh` | 742 | 128 | -0.9209 | -0.1647 | 0.4141 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `fresh_or_unflagged` | 228 | 57 | 1.8946 | 3.7223 | 0.614 | `candidate_recovery_or_relax` |
| `stale_bucket` | `stale_unknown` | 571 | 30 | -1.2253 | -0.091 | 0.4667 | `candidate_tighten_or_exclude` |
| `stale_bucket` | `stale_block` | 81 | 10 | -1.2771 | -1.157 | 0.1 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `risk_unknown` | 1216 | 175 | -1.0141 | -0.2335 | 0.4057 | `candidate_tighten_or_exclude` |
| `strength_bucket` | `strength_unknown` | 228 | 57 | 1.8946 | 3.7223 | 0.614 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_1000_1200` | 482 | 81 | -1.4082 | -0.2198 | 0.358 | `candidate_tighten_or_exclude` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_13`: `score_band` / `score_60_62` -> `candidate_tighten_or_exclude`
- `entry_bucket_14`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_15`: `score_band` / `score_lt60` -> `candidate_tighten_or_exclude`
- `entry_bucket_16`: `score_band` / `score_63_65` -> `candidate_recovery_or_relax`
- `entry_bucket_17`: `source_stage` / `scalp_entry_action_decision_snapshot` -> `candidate_tighten_or_exclude`
- `entry_bucket_18`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_19`: `stale_bucket` / `fresh` -> `candidate_tighten_or_exclude`
- `entry_bucket_20`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`
- `entry_bucket_25`: `time_bucket` / `time_1000_1200` -> `candidate_tighten_or_exclude`
- `entry_bucket_26`: `time_bucket` / `time_0900_1000` -> `candidate_tighten_or_exclude`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `NO_BUY_AI` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `combo_entry_spot` / `score=score_60_62|source=scalp_entry_action_decision_snapshot|stale=fresh|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_0900_1000` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `combo_entry_spot` / `score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_unknown|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_1000_1200` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `exit_rule` / `scalp_sim_panic_lifecycle_full_exit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `exit_rule` / `scalp_trailing_take_profit` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

## Scale-In Bucket Attribution

- decision_authority: `adm_ldm_scale_in_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'scale_in_rows': 37853, 'bucket_count': 2549, 'actionable_bucket_count': 207, 'runtime_candidate_count': 10, 'workorder_count': 10, 'arm_counts': {'AVG_DOWN': 21959, 'PYRAMID': 84, 'arm_unknown': 15810}}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `ai_score_band` | `score_lt60` | 16697 | 16697 | -0.1813 | -0.2021 | 0.3126 | `hold_no_edge` |
| `ai_score_band` | `score_60_62` | 8015 | 8015 | -0.1628 | -0.1842 | 0.2659 | `hold_no_edge` |
| `ai_score_band` | `score_66_69` | 6767 | 6767 | -0.0838 | -0.1085 | 0.3436 | `hold_no_edge` |
| `ai_score_band` | `score_63_65` | 4980 | 4980 | -0.1529 | -0.1716 | 0.311 | `hold_no_edge` |
| `ai_score_band` | `score_70p` | 1329 | 1329 | -0.0181 | -0.0508 | 0.4454 | `hold_no_edge` |
| `ai_score_band` | `score_unknown` | 65 | 0 | None | None | None | `hold_sample` |
| `ai_score_source` | `ai_source_unknown` | 37853 | 37788 | -0.1504 | -0.1722 | 0.3127 | `hold_no_edge` |
| `arm` | `AVG_DOWN` | 21959 | 21940 | -0.1595 | -0.1982 | 0.2823 | `hold_no_edge` |
| `arm` | `arm_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `arm` | `PYRAMID` | 84 | 38 | -13.3569 | -17.2682 | 0.7895 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `AVG_DOWN` | 19235 | 19228 | -0.129 | -0.1731 | 0.3221 | `hold_no_edge` |
| `blocker_namespace` | `blocker_namespace_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `blocker_namespace` | `AVG_DOWN_ONLY` | 2712 | 2712 | -0.3764 | -0.3764 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PYRAMID` | 52 | 38 | -13.3569 | -17.2682 | 0.7895 | `candidate_tighten_or_exclude` |
| `blocker_namespace` | `PRICE_GUARD` | 25 | 0 | None | None | None | `hold_sample` |
| `blocker_namespace` | `QTY_GUARD` | 19 | 0 | None | None | None | `hold_sample` |
| `blocker_reason` | `blocker_reason_unknown` | 15810 | 15810 | -0.1061 | -0.095 | 0.3538 | `hold_no_edge` |
| `blocker_reason` | `scale_in_probe_blocked` | 5701 | 5701 | -0.0047 | -0.0721 | 0.4047 | `hold_no_edge` |
| `blocker_reason` | `add_judgment_locked` | 3698 | 3698 | -0.296 | -0.2947 | 0.1152 | `hold_no_edge` |
| `blocker_reason` | `scale_in_gate_blocked` | 3409 | 3409 | -0.1647 | -0.2727 | 0.1297 | `hold_no_edge` |
| `blocker_reason` | `near_market_close` | 588 | 588 | -0.2298 | -0.2298 | 0.165 | `hold_no_edge` |
| `blocker_reason` | `scalping_cutoff` | 311 | 311 | -0.3178 | -0.3178 | 0.1061 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `low_broken` | 306 | 306 | -0.3391 | -0.3391 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.06)` | 125 | 125 | -0.06 | -0.06 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.07)` | 99 | 99 | -0.07 | -0.07 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.09)` | 96 | 96 | 0.09 | 0.09 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.11)` | 88 | 88 | 0.11 | 0.11 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.13)` | 80 | 80 | 0.13 | 0.13 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.28)` | 75 | 75 | 0.28 | 0.28 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.08)` | 70 | 70 | 0.08 | 0.08 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.23)` | 69 | 69 | 0.23 | 0.23 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.05)` | 68 | 68 | -0.05 | -0.05 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.01)` | 68 | 68 | 0.01 | 0.01 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.71)` | 65 | 65 | -0.71 | -0.71 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.73)` | 64 | 64 | -0.73 | -0.73 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(0.26)` | 60 | 60 | 0.26 | 0.26 | 1.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(-0.95)` | 58 | 58 | -0.95 | -0.95 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.72)` | 56 | 56 | -0.72 | -0.72 | 0.0 | `candidate_tighten_or_exclude` |
| `blocker_reason` | `pnl_out_of_range(-0.09)` | 52 | 52 | -0.09 | -0.09 | 0.0 | `hold_no_edge` |
| `blocker_reason` | `pnl_out_of_range(0.12)` | 52 | 52 | 0.12 | 0.12 | 1.0 | `hold_no_edge` |

### Scale-In Bucket Runtime Approval Candidates

- `scale_in_bucket_1`: `arm` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_2`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_3`: `blocker_namespace` / `PYRAMID` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_4`: `blocker_reason` / `scalping_cutoff` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_5`: `blocker_reason` / `low_broken` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_6`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_7`: `blocker_reason` / `pnl_out_of_range(-0.73)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_8`: `blocker_reason` / `pnl_out_of_range(-0.95)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_9`: `blocker_reason` / `pnl_out_of_range(-0.72)` -> `candidate_tighten_or_exclude`
- `scale_in_bucket_10`: `blocker_reason` / `pnl_out_of_range(0.32)` -> `candidate_recovery_or_relax`

### Scale-In Bucket Workorders

- `scale_in_bucket_source_quality_1`: `arm` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_2`: `blocker_namespace` / `AVG_DOWN_ONLY` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_3`: `blocker_namespace` / `PYRAMID` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_4`: `blocker_reason` / `scalping_cutoff` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_5`: `blocker_reason` / `low_broken` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_6`: `blocker_reason` / `pnl_out_of_range(-0.71)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_7`: `blocker_reason` / `pnl_out_of_range(-0.73)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_8`: `blocker_reason` / `pnl_out_of_range(-0.95)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_9`: `blocker_reason` / `pnl_out_of_range(-0.72)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`
- `scale_in_bucket_source_quality_10`: `blocker_reason` / `pnl_out_of_range(0.32)` -> `scale_in_arm_bucket_needs_source_quality_or_threshold_cycle_confirmation`

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
