# Swing Selection Funnel Report - 2026-05-27

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `19`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 1091 | 12 |
| `blocked_swing_gap` | 4003 | 3 |
| `blocked_swing_score_vpw` | 33794 | 19 |
| `gatekeeper_fast_reuse` | 126 | 2 |
| `gatekeeper_fast_reuse_bypass` | 966 | 12 |
| `gatekeeper_reject_cache_reuse` | 699 | 5 |
| `holding_flow_ofi_smoothing_applied` | 638 | 90 |
| `holding_started` | 11 | 1 |
| `market_regime_block` | 9661 | 19 |
| `market_regime_prior_observed` | 25224 | 19 |
| `swing_entry_micro_context_observed` | 34630 | 18 |
| `swing_probe_discarded` | 7715 | 19 |
| `swing_probe_entry_candidate` | 138 | 16 |
| `swing_probe_exit_signal` | 10 | 3 |
| `swing_probe_holding_started` | 138 | 16 |
| `swing_probe_scale_in_order_assumed_filled` | 25 | 13 |
| `swing_probe_sell_order_assumed_filled` | 10 | 3 |
| `swing_reentry_counterfactual_after_loss` | 57 | 4 |
| `swing_same_symbol_loss_reentry_blocked` | 16 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 4 |
| `swing_scale_in_micro_context_observed` | 37 | 14 |
| `swing_sim_buy_order_assumed_filled` | 88 | 13 |
| `swing_sim_holding_started` | 88 | 13 |
| `swing_sim_order_bundle_assumed_filled` | 88 | 13 |
| `swing_sim_scale_in_order_assumed_filled` | 37 | 14 |
| `swing_sim_sell_order_assumed_filled` | 5 | 2 |

## Top Code Stage

- `blocked_swing_score_vpw` GS(078930): 5387
- `blocked_swing_score_vpw` 대한항공(003490): 5386
- `swing_entry_micro_context_observed` GS(078930): 5386
- `swing_entry_micro_context_observed` 대한항공(003490): 5385
- `blocked_swing_score_vpw` 한국가스공사(036460): 5384
- `swing_entry_micro_context_observed` 한국가스공사(036460): 5384
- `blocked_swing_score_vpw` 현대위아(011210): 5382
- `blocked_swing_score_vpw` GS리테일(007070): 5382
- `swing_entry_micro_context_observed` GS리테일(007070): 5382
- `swing_entry_micro_context_observed` 현대위아(011210): 5381

## OFI/QI Micro Context

- sample_count: `70459`
- stale_missing_unique_record_count: `25`
- stale_missing_ratio: `0.0634`
- stale_missing_reason_counts: `{'micro_missing': 4470, 'micro_not_ready': 3835, 'state_insufficient': 3835, 'observer_unhealthy': 39}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 3796, 'micro_missing': 635, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 39}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11, 'micro_missing': 5}`
- stale_missing_group_counts: `{'entry': 3825, 'exit': 640, 'scale_in': 5}`
- stale_missing_group_unique_record_counts: `{'entry': 19, 'exit': 6, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 39, 'observer_unhealthy_with_other_reason': 39, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 61655, 'bearish': 1804, 'insufficient': 3825, 'bullish': 2423}`
- scale_in_micro_state_counts: `{'neutral': 89, 'insufficient': 5, 'bullish': 3, 'bearish': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 631, 'DEBOUNCE_EXIT': 5, 'CONFIRM_EXIT': 2}`
