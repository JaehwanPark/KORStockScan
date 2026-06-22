# Swing Selection Funnel Report - 2026-06-22

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `26`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 208 | 4 |
| `blocked_swing_gap` | 69 | 1 |
| `blocked_swing_score_vpw` | 620 | 6 |
| `gatekeeper_fast_reuse_bypass` | 208 | 4 |
| `gatekeeper_reject_cache_reuse` | 54 | 3 |
| `holding_flow_ofi_smoothing_applied` | 120 | 55 |
| `market_regime_prior_observed` | 828 | 8 |
| `swing_entry_micro_context_observed` | 793 | 7 |
| `swing_probe_discarded` | 1440 | 8 |
| `swing_probe_entry_candidate` | 9 | 7 |
| `swing_probe_exit_signal` | 10 | 9 |
| `swing_probe_holding_started` | 9 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_probe_sell_order_assumed_filled` | 10 | 9 |
| `swing_reentry_counterfactual_after_loss` | 45 | 2 |
| `swing_same_symbol_loss_reentry_blocked` | 12 | 2 |
| `swing_same_symbol_loss_reentry_cooldown` | 8 | 7 |
| `swing_scale_in_micro_context_observed` | 8 | 7 |
| `swing_sim_buy_order_assumed_filled` | 66 | 4 |
| `swing_sim_holding_started` | 66 | 4 |
| `swing_sim_order_bundle_assumed_filled` | 66 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_sim_sell_order_assumed_filled` | 2 | 2 |

## Top Code Stage

- `swing_probe_discarded` 삼성중공업(010140): 285
- `swing_probe_discarded` HJ중공업(097230): 281
- `swing_probe_discarded` 현대로템(064350): 272
- `swing_probe_discarded` 케이씨텍(281820): 212
- `swing_probe_discarded` 두산퓨얼셀(336260): 206
- `blocked_swing_score_vpw` 현대로템(064350): 128
- `market_regime_prior_observed` 현대로템(064350): 128
- `swing_entry_micro_context_observed` 현대로템(064350): 128
- `gatekeeper_fast_reuse_bypass` 두산퓨얼셀(336260): 128
- `blocked_gatekeeper_reject` 두산퓨얼셀(336260): 128

## OFI/QI Micro Context

- sample_count: `1921`
- stale_missing_unique_record_count: `10`
- stale_missing_ratio: `0.0947`
- stale_missing_reason_counts: `{'micro_missing': 182, 'micro_not_ready': 63, 'state_insufficient': 63}`
- stale_missing_reason_combination_counts: `{'micro_missing': 119, 'micro_missing+micro_not_ready+state_insufficient': 63}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 10}`
- stale_missing_group_counts: `{'exit': 123, 'entry': 59}`
- stale_missing_group_unique_record_counts: `{'entry': 8, 'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 1586, 'bullish': 80, 'bearish': 40, 'insufficient': 59}`
- scale_in_micro_state_counts: `{'neutral': 24}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 120}`
