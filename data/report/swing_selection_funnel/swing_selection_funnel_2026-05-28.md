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
| `blocked_gatekeeper_reject` | 3964 | 10 |
| `blocked_swing_gap` | 1105 | 4 |
| `blocked_swing_score_vpw` | 10296 | 18 |
| `gatekeeper_fast_reuse` | 463 | 4 |
| `gatekeeper_fast_reuse_bypass` | 3501 | 10 |
| `gatekeeper_reject_cache_reuse` | 3179 | 9 |
| `holding_flow_ofi_smoothing_applied` | 532 | 79 |
| `market_regime_block` | 10383 | 18 |
| `market_regime_prior_observed` | 3877 | 18 |
| `swing_entry_micro_context_observed` | 14194 | 13 |
| `swing_probe_discarded` | 2658 | 15 |
| `swing_probe_entry_candidate` | 10 | 8 |
| `swing_probe_exit_signal` | 10 | 8 |
| `swing_probe_holding_started` | 10 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 8 | 8 |
| `swing_probe_sell_order_assumed_filled` | 10 | 8 |
| `swing_reentry_counterfactual_after_loss` | 17 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 5 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 5 | 4 |
| `swing_scale_in_micro_context_observed` | 15 | 11 |
| `swing_sim_buy_order_assumed_filled` | 10 | 5 |
| `swing_sim_holding_started` | 10 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 10 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 11 |
| `swing_sim_sell_order_assumed_filled` | 2 | 1 |

## Top Code Stage

- `swing_entry_micro_context_observed` 대한항공(003490): 1995
- `swing_entry_micro_context_observed` 한국타이어앤테크놀로지(161390): 1995
- `blocked_swing_score_vpw` 현대해상(001450): 1995
- `swing_entry_micro_context_observed` 현대해상(001450): 1995
- `swing_entry_micro_context_observed` 대한전선(001440): 1995
- `blocked_gatekeeper_reject` 한국타이어앤테크놀로지(161390): 1994
- `blocked_swing_score_vpw` 드림텍(192650): 1994
- `swing_entry_micro_context_observed` 드림텍(192650): 1994
- `gatekeeper_fast_reuse_bypass` 한국타이어앤테크놀로지(161390): 1731
- `gatekeeper_reject_cache_reuse` 한국타이어앤테크놀로지(161390): 1594

## OFI/QI Micro Context

- sample_count: `29061`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.1267`
- stale_missing_reason_counts: `{'micro_missing': 3682, 'micro_not_ready': 3154, 'state_insufficient': 3154, 'observer_unhealthy': 8}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 3146, 'micro_missing': 528, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing': 1, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'entry': 3147, 'exit': 532, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'entry': 14, 'exit': 1, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 23916, 'bearish': 826, 'insufficient': 3147, 'bullish': 590}`
- scale_in_micro_state_counts: `{'neutral': 35, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 532}`
