# Swing Selection Funnel Report - 2026-06-02

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `16`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 8916 | 7 |
| `blocked_swing_gap` | 713 | 3 |
| `blocked_swing_score_vpw` | 17032 | 15 |
| `gatekeeper_fast_reuse` | 955 | 3 |
| `gatekeeper_fast_reuse_bypass` | 7961 | 7 |
| `gatekeeper_reject_cache_reuse` | 7457 | 3 |
| `holding_flow_ofi_smoothing_applied` | 936 | 112 |
| `holding_started` | 1 | 1 |
| `market_regime_block` | 17588 | 16 |
| `market_regime_prior_observed` | 8359 | 16 |
| `swing_entry_micro_context_observed` | 25732 | 7 |
| `swing_probe_discarded` | 6139 | 14 |
| `swing_probe_entry_candidate` | 16 | 10 |
| `swing_probe_exit_signal` | 16 | 13 |
| `swing_probe_holding_started` | 16 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 9 |
| `swing_probe_sell_order_assumed_filled` | 16 | 13 |
| `swing_reentry_counterfactual_after_loss` | 42 | 6 |
| `swing_same_symbol_loss_reentry_blocked` | 5 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 8 |
| `swing_scale_in_micro_context_observed` | 11 | 10 |
| `swing_sim_buy_order_assumed_filled` | 8 | 5 |
| `swing_sim_holding_started` | 8 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 8 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 10 |

## Top Code Stage

- `blocked_gatekeeper_reject` 두산퓨얼셀(336260): 6029
- `swing_entry_micro_context_observed` 두산퓨얼셀(336260): 6029
- `blocked_swing_score_vpw` 한화엔진(082740): 5552
- `swing_entry_micro_context_observed` 한화엔진(082740): 5549
- `gatekeeper_fast_reuse_bypass` 두산퓨얼셀(336260): 5284
- `gatekeeper_reject_cache_reuse` 두산퓨얼셀(336260): 4979
- `swing_entry_micro_context_observed` 대한항공(003490): 4007
- `blocked_swing_score_vpw` 대한항공(003490): 4007
- `blocked_swing_score_vpw` 한국타이어앤테크놀로지(161390): 3679
- `swing_entry_micro_context_observed` 한국타이어앤테크놀로지(161390): 3677

## OFI/QI Micro Context

- sample_count: `52692`
- stale_missing_unique_record_count: `32`
- stale_missing_ratio: `0.1219`
- stale_missing_reason_counts: `{'micro_missing': 6423, 'micro_not_ready': 5496, 'state_insufficient': 5496, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 927, 'micro_missing+micro_not_ready+state_insufficient': 5495, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 16, 'micro_missing+micro_not_ready+state_insufficient': 16, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 936, 'entry': 5487}`
- stale_missing_group_unique_record_counts: `{'exit': 16, 'entry': 16}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 43485, 'bearish': 1489, 'bullish': 1248, 'insufficient': 5487}`
- scale_in_micro_state_counts: `{'neutral': 28, 'bullish': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 928, 'CONFIRM_EXIT': 8}`
