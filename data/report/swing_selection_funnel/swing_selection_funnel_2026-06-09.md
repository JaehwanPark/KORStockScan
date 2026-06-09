# Swing Selection Funnel Report - 2026-06-09

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `2`
- fallback_written_to_recommendations: `False`
- csv_rows: `2`
- db_rows: `9`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 8377 | 8 |
| `blocked_swing_gap` | 11055 | 7 |
| `blocked_swing_score_vpw` | 4720 | 7 |
| `gatekeeper_fast_reuse` | 321 | 5 |
| `gatekeeper_fast_reuse_bypass` | 8057 | 8 |
| `gatekeeper_reject_cache_reuse` | 7359 | 7 |
| `holding_flow_ofi_smoothing_applied` | 657 | 104 |
| `market_regime_prior_observed` | 13097 | 9 |
| `swing_entry_micro_context_observed` | 13049 | 7 |
| `swing_probe_discarded` | 5229 | 8 |
| `swing_probe_entry_candidate` | 18 | 8 |
| `swing_probe_exit_signal` | 18 | 13 |
| `swing_probe_holding_started` | 18 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 7 |
| `swing_probe_sell_order_assumed_filled` | 18 | 13 |
| `swing_reentry_counterfactual_after_loss` | 15 | 2 |
| `swing_same_symbol_loss_reentry_blocked` | 1 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 3 |
| `swing_scale_in_micro_context_observed` | 70 | 9 |
| `swing_sim_buy_order_assumed_filled` | 13 | 7 |
| `swing_sim_holding_started` | 13 | 7 |
| `swing_sim_order_bundle_assumed_filled` | 13 | 7 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 8 |

## Top Code Stage

- `market_regime_prior_observed` 유진투자증권(001200): 3444
- `swing_entry_micro_context_observed` 유진투자증권(001200): 3444
- `blocked_gatekeeper_reject` 유진투자증권(001200): 3443
- `market_regime_prior_observed` JB금융지주(175330): 3441
- `swing_entry_micro_context_observed` JB금융지주(175330): 3441
- `blocked_swing_score_vpw` JB금융지주(175330): 3375
- `blocked_swing_gap` 유진투자증권(001200): 3356
- `gatekeeper_fast_reuse_bypass` 유진투자증권(001200): 3253
- `blocked_swing_gap` JB금융지주(175330): 3240
- `blocked_gatekeeper_reject` 카카오뱅크(323410): 3089

## OFI/QI Micro Context

- sample_count: `26948`
- stale_missing_unique_record_count: `6`
- stale_missing_ratio: `0.4687`
- stale_missing_reason_counts: `{'micro_missing': 12630, 'micro_not_ready': 11983, 'state_insufficient': 11983}`
- stale_missing_reason_combination_counts: `{'micro_missing': 647, 'micro_missing+micro_not_ready+state_insufficient': 11983}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing': 2}`
- stale_missing_group_counts: `{'exit': 659, 'entry': 11959, 'scale_in': 12}`
- stale_missing_group_unique_record_counts: `{'entry': 4, 'scale_in': 1, 'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 13236, 'bearish': 666, 'bullish': 315, 'insufficient': 11959}`
- scale_in_micro_state_counts: `{'neutral': 80, 'insufficient': 12, 'bearish': 4, 'bullish': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 648, 'CONFIRM_EXIT': 1, 'DEBOUNCE_EXIT': 8}`
