# Swing Selection Funnel Report - 2026-06-05

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
| `blocked_gatekeeper_reject` | 723 | 5 |
| `blocked_swing_gap` | 4854 | 6 |
| `blocked_swing_score_vpw` | 22972 | 16 |
| `gatekeeper_fast_reuse` | 28 | 2 |
| `gatekeeper_fast_reuse_bypass` | 695 | 5 |
| `gatekeeper_reject_cache_reuse` | 651 | 3 |
| `holding_flow_ofi_smoothing_applied` | 482 | 56 |
| `market_regime_block` | 23589 | 16 |
| `market_regime_prior_observed` | 106 | 16 |
| `swing_entry_micro_context_observed` | 23486 | 8 |
| `swing_probe_discarded` | 4408 | 15 |
| `swing_probe_entry_candidate` | 19 | 12 |
| `swing_probe_exit_signal` | 19 | 14 |
| `swing_probe_holding_started` | 19 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 9 |
| `swing_probe_sell_order_assumed_filled` | 19 | 14 |
| `swing_reentry_counterfactual_after_loss` | 46 | 7 |
| `swing_same_symbol_loss_reentry_blocked` | 6 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 14 | 12 |
| `swing_scale_in_micro_context_observed` | 186 | 10 |
| `swing_sim_buy_order_assumed_filled` | 15 | 8 |
| `swing_sim_holding_started` | 15 | 8 |
| `swing_sim_order_bundle_assumed_filled` | 15 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 14 | 9 |
| `swing_sim_sell_order_assumed_filled` | 6 | 4 |

## Top Code Stage

- `blocked_swing_score_vpw` GS(078930): 6888
- `swing_entry_micro_context_observed` GS(078930): 6888
- `market_regime_block` GS(078930): 6869
- `swing_entry_micro_context_observed` 케이뱅크(279570): 6391
- `market_regime_block` 케이뱅크(279570): 6372
- `blocked_swing_score_vpw` 케이뱅크(279570): 5688
- `blocked_swing_score_vpw` 한국앤컴퍼니(000240): 5545
- `swing_entry_micro_context_observed` 한국앤컴퍼니(000240): 5544
- `market_regime_block` 한국앤컴퍼니(000240): 5526
- `swing_entry_micro_context_observed` 한올바이오파마(009420): 4628

## OFI/QI Micro Context

- sample_count: `47943`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.0725`
- stale_missing_reason_counts: `{'micro_missing': 3474, 'micro_not_ready': 2999, 'state_insufficient': 2999, 'observer_unhealthy': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2993, 'micro_missing': 475, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3, 'micro_missing': 1}`
- stale_missing_group_counts: `{'entry': 2992, 'exit': 482}`
- stale_missing_group_unique_record_counts: `{'entry': 15, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 41093, 'bearish': 1565, 'bullish': 1575, 'insufficient': 2992}`
- scale_in_micro_state_counts: `{'bearish': 14, 'neutral': 196, 'bullish': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 478, 'CONFIRM_EXIT': 4}`
