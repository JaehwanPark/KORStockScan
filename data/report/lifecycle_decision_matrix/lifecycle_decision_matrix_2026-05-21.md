# Lifecycle Decision Matrix - 2026-05-21

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-21`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `14473`
- source_rows_total: `14473`
- retained_rows: `14473`
- dropped_rows_by_source: `{}`
- joined_rows: `14072`
- policy_pass_count: `5`
- promote_ready_count: `1`
- entry_bucket_actionable_count: `10`
- entry_bucket_runtime_candidate_count: `3`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 198 | 35 | 1.0419 | 0.6187 | `pass` | `BUY_DEFENSIVE` | True |
| `submit` | 174 | 153 | -0.9449 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 174 | 153 | -0.6074 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 13050 | 13050 | -0.0799 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 877 | 681 | -0.4945 | 1.0 | `pass` | `EXIT` | False |

## Entry Bucket Attribution

- decision_authority: `adm_ldm_entry_bucket_attribution_source_only`
- primary_decision_metric: `source_quality_adjusted_ev_pct`
- summary: `{'entry_rows': 198, 'bucket_count': 25, 'actionable_bucket_count': 10, 'runtime_candidate_count': 3, 'workorder_count': 10}`

| bucket_type | bucket_key | sample | joined | ev | avg_profit | win_rate | route |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `chosen_action` | `action_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 26 | 26 | 0.8939 | 2.6115 | 0.6923 | `candidate_recovery_or_relax` |
| `combo_entry_spot` | `score=score_63_65|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 7 | 7 | 2.4366 | 4.1968 | 0.5714 | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 2 | 2 | -1.9159 | -0.5849 | 0.0 | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_bottoming_entry_allowed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 5 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_60_62|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 114 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_63_65|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 10 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_sim_panic_bottoming_entry_allowed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 2 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_66_69|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 14 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_70p|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 1 | 0 | None | None | None | `hold_sample` |
| `combo_entry_spot` | `score=score_lt60|source=scalp_sim_panic_level1_entry_observed|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` | 17 | 0 | None | None | None | `hold_sample` |
| `exit_rule` | `exit_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `liquidity_bucket` | `liquidity_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `overbought_bucket` | `overbought_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `score_band` | `score_66_69` | 42 | 26 | 0.8939 | 2.6115 | 0.6923 | `candidate_recovery_or_relax` |
| `score_band` | `score_63_65` | 17 | 7 | 2.4366 | 4.1968 | 0.5714 | `hold_sample` |
| `score_band` | `score_70p` | 3 | 2 | -1.9159 | -0.5849 | 0.0 | `hold_sample` |
| `score_band` | `score_60_62` | 119 | 0 | None | None | None | `hold_sample` |
| `score_band` | `score_lt60` | 17 | 0 | None | None | None | `hold_sample` |
| `source_stage` | `wait6579_ev_cohort` | 35 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `stale_bucket` | `fresh_or_unflagged` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `strength_bucket` | `strength_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |
| `time_bucket` | `time_unknown` | 198 | 35 | 1.0419 | 2.7459 | 0.6286 | `candidate_recovery_or_relax` |

### Entry Bucket Runtime Approval Candidates

- `entry_bucket_6`: `score_band` / `score_66_69` -> `candidate_recovery_or_relax`
- `entry_bucket_7`: `source_stage` / `wait6579_ev_cohort` -> `candidate_recovery_or_relax`
- `entry_bucket_8`: `stale_bucket` / `fresh_or_unflagged` -> `candidate_recovery_or_relax`

### Entry Bucket Workorders

- `entry_bucket_source_quality_1`: `chosen_action` / `action_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_2`: `combo_entry_spot` / `score=score_66_69|source=wait6579_ev_cohort|stale=fresh_or_unflagged|liquidity=liquidity_unknown|overbought=overbought_unknown|time=time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_3`: `exit_rule` / `exit_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_4`: `liquidity_bucket` / `liquidity_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_5`: `overbought_bucket` / `overbought_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_6`: `score_band` / `score_66_69` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_7`: `source_stage` / `wait6579_ev_cohort` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_8`: `stale_bucket` / `fresh_or_unflagged` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_9`: `strength_bucket` / `strength_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`
- `entry_bucket_source_quality_10`: `time_bucket` / `time_unknown` -> `bucket_has_edge_but_needs_rolling_or_feature_confirmation`

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
