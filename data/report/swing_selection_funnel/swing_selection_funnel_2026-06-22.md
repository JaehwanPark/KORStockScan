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
| `blocked_gatekeeper_reject` | 201 | 4 |
| `blocked_swing_gap` | 69 | 1 |
| `blocked_swing_score_vpw` | 612 | 6 |
| `gatekeeper_fast_reuse_bypass` | 201 | 4 |
| `gatekeeper_reject_cache_reuse` | 50 | 3 |
| `holding_flow_ofi_smoothing_applied` | 103 | 52 |
| `market_regime_prior_observed` | 813 | 8 |
| `swing_entry_micro_context_observed` | 779 | 7 |
| `swing_probe_discarded` | 1413 | 8 |
| `swing_probe_entry_candidate` | 8 | 7 |
| `swing_probe_exit_signal` | 8 | 7 |
| `swing_probe_holding_started` | 8 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_probe_sell_order_assumed_filled` | 8 | 7 |
| `swing_reentry_counterfactual_after_loss` | 45 | 2 |
| `swing_same_symbol_loss_reentry_blocked` | 12 | 2 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_scale_in_micro_context_observed` | 8 | 7 |
| `swing_sim_buy_order_assumed_filled` | 66 | 4 |
| `swing_sim_holding_started` | 66 | 4 |
| `swing_sim_order_bundle_assumed_filled` | 66 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 8 | 7 |
| `swing_sim_sell_order_assumed_filled` | 2 | 2 |

## Top Code Stage

- `swing_probe_discarded` 삼성중공업(010140): 285
- `swing_probe_discarded` HJ중공업(097230): 281
- `swing_probe_discarded` 현대로템(064350): 260
- `swing_probe_discarded` 케이씨텍(281820): 212
- `swing_probe_discarded` 두산퓨얼셀(336260): 194
- `market_regime_prior_observed` 삼성중공업(010140): 121
- `swing_entry_micro_context_observed` 삼성중공업(010140): 121
- `market_regime_prior_observed` 제일기획(030000): 121
- `swing_entry_micro_context_observed` 제일기획(030000): 121
- `blocked_swing_score_vpw` 현대로템(064350): 121

## OFI/QI Micro Context

- sample_count: `1873`
- stale_missing_unique_record_count: `7`
- stale_missing_ratio: `0.0769`
- stale_missing_reason_counts: `{'micro_missing': 144, 'micro_not_ready': 42, 'state_insufficient': 42}`
- stale_missing_reason_combination_counts: `{'micro_missing': 102, 'micro_missing+micro_not_ready+state_insufficient': 42}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'exit': 104, 'entry': 40}`
- stale_missing_group_unique_record_counts: `{'entry': 7, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 1576, 'bullish': 80, 'bearish': 40, 'insufficient': 40}`
- scale_in_micro_state_counts: `{'neutral': 24}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 103}`
