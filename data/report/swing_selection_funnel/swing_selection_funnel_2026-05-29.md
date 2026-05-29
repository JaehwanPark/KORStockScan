# Swing Selection Funnel Report - 2026-05-29

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `18`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2945 | 10 |
| `blocked_swing_gap` | 3512 | 8 |
| `blocked_swing_score_vpw` | 11877 | 17 |
| `gatekeeper_fast_reuse` | 101 | 5 |
| `gatekeeper_fast_reuse_bypass` | 2846 | 10 |
| `gatekeeper_reject_cache_reuse` | 2603 | 8 |
| `holding_flow_ofi_smoothing_applied` | 621 | 81 |
| `market_regime_prior_observed` | 14822 | 18 |
| `swing_entry_micro_context_observed` | 14638 | 12 |
| `swing_probe_discarded` | 3350 | 15 |
| `swing_probe_entry_candidate` | 21 | 12 |
| `swing_probe_exit_signal` | 14 | 9 |
| `swing_probe_holding_started` | 21 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 8 |
| `swing_probe_sell_order_assumed_filled` | 14 | 9 |
| `swing_reentry_counterfactual_after_loss` | 44 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 12 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_scale_in_micro_context_observed` | 25 | 12 |
| `swing_sim_buy_order_assumed_filled` | 44 | 10 |
| `swing_sim_holding_started` | 44 | 10 |
| `swing_sim_order_bundle_assumed_filled` | 44 | 10 |
| `swing_sim_scale_in_order_assumed_filled` | 25 | 12 |
| `swing_sim_sell_order_assumed_filled` | 8 | 4 |

## Top Code Stage

- `blocked_swing_score_vpw` 한화엔진(082740): 3250
- `market_regime_prior_observed` 한화엔진(082740): 3250
- `swing_entry_micro_context_observed` 한화엔진(082740): 3250
- `blocked_swing_score_vpw` 대한항공(003490): 3218
- `market_regime_prior_observed` 대한항공(003490): 3218
- `swing_entry_micro_context_observed` 대한항공(003490): 3218
- `market_regime_prior_observed` HL만도(204320): 3082
- `swing_entry_micro_context_observed` HL만도(204320): 3080
- `blocked_swing_gap` 한온시스템(018880): 2911
- `market_regime_prior_observed` 한온시스템(018880): 2911

## OFI/QI Micro Context

- sample_count: `30264`
- stale_missing_unique_record_count: `20`
- stale_missing_ratio: `0.1157`
- stale_missing_reason_counts: `{'micro_missing': 3501, 'micro_not_ready': 2890, 'state_insufficient': 2890, 'observer_unhealthy': 8}`
- stale_missing_reason_combination_counts: `{'micro_missing': 611, 'micro_missing+micro_not_ready+state_insufficient': 2882, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 3, 'micro_missing+micro_not_ready+state_insufficient': 17, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'exit': 621, 'entry': 2880}`
- stale_missing_group_unique_record_counts: `{'exit': 3, 'entry': 17}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'bearish': 843, 'neutral': 25309, 'bullish': 528, 'insufficient': 2880}`
- scale_in_micro_state_counts: `{'neutral': 55, 'bearish': 4, 'bullish': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 610, 'CONFIRM_EXIT': 11}`
