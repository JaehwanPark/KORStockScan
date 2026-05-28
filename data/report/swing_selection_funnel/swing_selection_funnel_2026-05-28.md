# Swing Selection Funnel Report - 2026-05-28

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
| `blocked_gatekeeper_reject` | 5311 | 10 |
| `blocked_swing_gap` | 1491 | 4 |
| `blocked_swing_score_vpw` | 14364 | 18 |
| `gatekeeper_fast_reuse` | 634 | 4 |
| `gatekeeper_fast_reuse_bypass` | 4677 | 10 |
| `gatekeeper_reject_cache_reuse` | 4295 | 9 |
| `holding_flow_ofi_smoothing_applied` | 607 | 84 |
| `holding_started` | 1 | 1 |
| `market_regime_block` | 14954 | 18 |
| `market_regime_prior_observed` | 4721 | 18 |
| `swing_entry_micro_context_observed` | 19580 | 13 |
| `swing_probe_discarded` | 3458 | 15 |
| `swing_probe_entry_candidate` | 15 | 8 |
| `swing_probe_exit_signal` | 15 | 11 |
| `swing_probe_holding_started` | 15 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 15 | 11 |
| `swing_reentry_counterfactual_after_loss` | 27 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 7 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 7 | 6 |
| `swing_scale_in_micro_context_observed` | 16 | 11 |
| `swing_sim_buy_order_assumed_filled` | 27 | 13 |
| `swing_sim_holding_started` | 27 | 13 |
| `swing_sim_order_bundle_assumed_filled` | 27 | 13 |
| `swing_sim_scale_in_order_assumed_filled` | 16 | 11 |
| `swing_sim_sell_order_assumed_filled` | 2 | 1 |

## Top Code Stage

- `swing_entry_micro_context_observed` 한국타이어앤테크놀로지(161390): 2665
- `blocked_swing_score_vpw` 현대해상(001450): 2665
- `swing_entry_micro_context_observed` 현대해상(001450): 2665
- `swing_entry_micro_context_observed` 대한전선(001440): 2665
- `swing_entry_micro_context_observed` 대한항공(003490): 2664
- `blocked_gatekeeper_reject` 한국타이어앤테크놀로지(161390): 2664
- `blocked_swing_score_vpw` 드림텍(192650): 2664
- `swing_entry_micro_context_observed` 드림텍(192650): 2664
- `gatekeeper_fast_reuse_bypass` 한국타이어앤테크놀로지(161390): 2336
- `blocked_swing_score_vpw` 대한항공(003490): 2172

## OFI/QI Micro Context

- sample_count: `39982`
- stale_missing_unique_record_count: `20`
- stale_missing_ratio: `0.117`
- stale_missing_reason_counts: `{'micro_missing': 4677, 'micro_not_ready': 4078, 'state_insufficient': 4078, 'observer_unhealthy': 8}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4070, 'micro_missing': 599, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing': 2, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'entry': 4067, 'exit': 607, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'entry': 17, 'exit': 2, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 33232, 'bearish': 1109, 'insufficient': 4067, 'bullish': 910}`
- scale_in_micro_state_counts: `{'neutral': 37, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 607}`
