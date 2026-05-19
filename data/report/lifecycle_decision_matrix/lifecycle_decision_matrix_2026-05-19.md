# Lifecycle Decision Matrix - 2026-05-19

## Contract
- matrix_version: `lifecycle_decision_matrix_v1_2026-05-19`
- runtime_effect: `False`
- decision_authority: `weighted_adm_source_bundle_for_auto_bounded_apply`
- primary_decision_metric: `stage_ev_composite_pct`

## Summary
- total_rows: `17`
- joined_rows: `15`
- policy_pass_count: `0`
- promote_ready_count: `0`
- warnings: `['all_stage_policy_entries_below_sample_floor']`

## Policy Entries
| stage | sample | joined | ev | confidence | source_quality | action | promote_ready |
| --- | ---: | ---: | ---: | ---: | --- | --- | --- |
| `entry` | 14 | 14 | 2.5281 | 1.0 | `hold_sample` | `BUY_DEFENSIVE` | False |
| `submit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `holding` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |
| `scale_in` | 3 | 1 | 1.386 | 0.0333 | `hold_sample` | `PYRAMID_BIAS` | False |
| `exit` | 0 | 0 | None | 0.0 | `hold_sample` | `NO_CHANGE` | False |

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
