# Swing Selection Funnel Report - 2026-06-18

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `21`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 397 | 10 |
| `blocked_swing_gap` | 23 | 2 |
| `blocked_swing_score_vpw` | 3395 | 21 |
| `gatekeeper_fast_reuse` | 20 | 5 |
| `gatekeeper_fast_reuse_bypass` | 378 | 10 |
| `gatekeeper_reject_cache_reuse` | 278 | 9 |
| `holding_flow_ofi_smoothing_applied` | 459 | 97 |
| `market_regime_pass` | 158 | 21 |
| `market_regime_prior_observed` | 3634 | 21 |
| `swing_entry_micro_context_observed` | 3714 | 20 |
| `swing_probe_discarded` | 1554 | 20 |
| `swing_probe_entry_candidate` | 10 | 9 |
| `swing_probe_exit_signal` | 10 | 10 |
| `swing_probe_holding_started` | 10 | 9 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 10 | 10 |
| `swing_reentry_counterfactual_after_loss` | 74 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 21 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 11 | 10 |
| `swing_scale_in_micro_context_observed` | 141 | 21 |
| `swing_sim_buy_order_assumed_filled` | 350 | 20 |
| `swing_sim_holding_started` | 350 | 20 |
| `swing_sim_order_bundle_assumed_filled` | 350 | 20 |
| `swing_sim_scale_in_order_assumed_filled` | 53 | 19 |
| `swing_sim_sell_order_assumed_filled` | 16 | 7 |

## Top Code Stage

- `blocked_swing_score_vpw` 한온시스템(018880): 706
- `swing_entry_micro_context_observed` 한온시스템(018880): 706
- `market_regime_prior_observed` 한온시스템(018880): 697
- `swing_entry_micro_context_observed` 코웨이(021240): 390
- `market_regime_prior_observed` 코웨이(021240): 389
- `swing_entry_micro_context_observed` 현대해상(001450): 372
- `market_regime_prior_observed` 현대해상(001450): 354
- `blocked_swing_score_vpw` HMM(011200): 349
- `swing_entry_micro_context_observed` HMM(011200): 348
- `market_regime_prior_observed` HMM(011200): 346

## OFI/QI Micro Context

- sample_count: `8917`
- stale_missing_unique_record_count: `31`
- stale_missing_ratio: `0.2014`
- stale_missing_reason_counts: `{'micro_missing': 1796, 'observer_unhealthy': 444, 'micro_not_ready': 1101, 'state_insufficient': 1101}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 200, 'micro_missing': 451, 'micro_missing+micro_not_ready+state_insufficient': 901, 'micro_missing+observer_unhealthy': 244}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16, 'micro_missing+micro_not_ready+state_insufficient': 22, 'micro_missing': 8, 'micro_missing+observer_unhealthy': 22}`
- stale_missing_group_counts: `{'exit': 467, 'entry': 1328, 'scale_in': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 14, 'entry': 21, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 444, 'observer_unhealthy_with_other_reason': 444, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 6677, 'bearish': 155, 'bullish': 306, 'insufficient': 1092}`
- scale_in_micro_state_counts: `{'neutral': 187, 'bullish': 7, 'insufficient': 1, 'bearish': 7}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 457, 'CONFIRM_EXIT': 2}`
