# Lifecycle Decision Matrix - 2026-05-20

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-20`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `7155`
- source_rows_total: `7155`
- retained_rows: `7155`
- dropped_rows_by_source: `{}`
- joined_rows: `6109`
- policy_pass_count: `5`
- promote_ready_count: `0`
- lifecycle_ai_context_feedback: `{'implementation_status': 'implemented', 'runtime_effect': False, 'decision_authority': 'lifecycle_ai_context_feedback_source_only', 'policy_entry_count': 5, 'bounded_auxiliary_weight_nonzero_count': 0, 'route_counts': {'hold_sample': 5}, 'quality_counts': {'hold_sample': 5}}`
- warnings: `[]`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 1143 | 179 | -0.0239 | 1.0 | `pass` | `WAIT_REQUOTE` | False |
| `submit` | 239 | 238 | -0.6133 | 1.0 | `pass` | `NO_CHANGE` | False |
| `holding` | 238 | 238 | -0.5938 | 1.0 | `pass` | `EXIT` | False |
| `scale_in` | 4795 | 4795 | -0.1753 | 1.0 | `pass` | `NO_CHANGE` | False |
| `exit` | 740 | 659 | -0.5419 | 1.0 | `pass` | `EXIT` | False |

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
