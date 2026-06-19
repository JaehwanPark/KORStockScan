# Swing Selection Funnel Report - 2026-06-19

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `20`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 332 | 14 |
| `blocked_swing_gap` | 130 | 6 |
| `blocked_swing_score_vpw` | 682 | 19 |
| `gatekeeper_fast_reuse_bypass` | 335 | 14 |
| `gatekeeper_reject_cache_reuse` | 26 | 10 |
| `holding_flow_ofi_smoothing_applied` | 68 | 40 |
| `market_regime_block` | 104 | 19 |
| `market_regime_prior_observed` | 910 | 20 |
| `swing_entry_micro_context_observed` | 987 | 20 |
| `swing_probe_discarded` | 1194 | 16 |
| `swing_probe_entry_candidate` | 14 | 9 |
| `swing_probe_exit_signal` | 14 | 11 |
| `swing_probe_holding_started` | 14 | 9 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 9 |
| `swing_probe_sell_order_assumed_filled` | 14 | 11 |
| `swing_reentry_counterfactual_after_loss` | 84 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 28 | 7 |
| `swing_same_symbol_loss_reentry_cooldown` | 13 | 11 |
| `swing_scale_in_micro_context_observed` | 27 | 16 |
| `swing_sim_buy_order_assumed_filled` | 133 | 20 |
| `swing_sim_holding_started` | 133 | 20 |
| `swing_sim_order_bundle_assumed_filled` | 133 | 20 |
| `swing_sim_scale_in_order_assumed_filled` | 22 | 16 |

## Top Code Stage

- `swing_probe_discarded` LS(006260): 174
- `swing_probe_discarded` HJ중공업(097230): 145
- `swing_probe_discarded` HD현대마린솔루션(443060): 142
- `swing_probe_discarded` DN오토모티브(007340): 137
- `swing_probe_discarded` 하이브(352820): 121
- `swing_probe_discarded` 코웨이(021240): 97
- `swing_probe_discarded` HMM(011200): 96
- `swing_probe_discarded` 산일전기(062040): 95
- `blocked_swing_score_vpw` 한화생명(088350): 72
- `swing_entry_micro_context_observed` 한화생명(088350): 72

## OFI/QI Micro Context

- sample_count: `2438`
- stale_missing_unique_record_count: `21`
- stale_missing_ratio: `0.0689`
- stale_missing_reason_counts: `{'micro_missing': 168, 'micro_not_ready': 100, 'state_insufficient': 100}`
- stale_missing_reason_combination_counts: `{'micro_missing': 68, 'micro_missing+micro_not_ready+state_insufficient': 100}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 1, 'micro_missing+micro_not_ready+state_insufficient': 20}`
- stale_missing_group_counts: `{'exit': 68, 'entry': 100}`
- stale_missing_group_unique_record_counts: `{'exit': 1, 'entry': 20}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 2073, 'bearish': 78, 'bullish': 44, 'insufficient': 100}`
- scale_in_micro_state_counts: `{'neutral': 61}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 68}`
