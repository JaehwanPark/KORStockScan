# Swing Selection Funnel Report - 2026-06-01

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `7`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 4136 | 2 |
| `blocked_swing_gap` | 4214 | 3 |
| `blocked_swing_score_vpw` | 18696 | 7 |
| `gatekeeper_fast_reuse` | 705 | 1 |
| `gatekeeper_fast_reuse_bypass` | 3431 | 2 |
| `gatekeeper_reject_cache_reuse` | 3171 | 2 |
| `holding_flow_ofi_smoothing_applied` | 1168 | 111 |
| `market_regime_prior_observed` | 22832 | 7 |
| `swing_entry_micro_context_observed` | 22783 | 5 |
| `swing_probe_discarded` | 5132 | 7 |
| `swing_probe_entry_candidate` | 25 | 7 |
| `swing_probe_exit_signal` | 18 | 6 |
| `swing_probe_holding_started` | 25 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 15 | 6 |
| `swing_probe_sell_order_assumed_filled` | 18 | 6 |
| `swing_reentry_counterfactual_after_loss` | 25 | 4 |
| `swing_same_symbol_loss_reentry_blocked` | 4 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 5 | 4 |
| `swing_scale_in_micro_context_observed` | 15 | 6 |
| `swing_sim_buy_order_assumed_filled` | 5 | 5 |
| `swing_sim_holding_started` | 5 | 5 |
| `swing_sim_order_bundle_assumed_filled` | 5 | 5 |
| `swing_sim_scale_in_order_assumed_filled` | 15 | 6 |

## Top Code Stage

- `blocked_swing_score_vpw` 한화엔진(082740): 5285
- `market_regime_prior_observed` 한화엔진(082740): 5285
- `swing_entry_micro_context_observed` 한화엔진(082740): 5285
- `blocked_swing_score_vpw` 한국타이어앤테크놀로지(161390): 5284
- `market_regime_prior_observed` 한국타이어앤테크놀로지(161390): 5284
- `swing_entry_micro_context_observed` 한국타이어앤테크놀로지(161390): 5283
- `market_regime_prior_observed` STX엔진(077970): 4376
- `swing_entry_micro_context_observed` STX엔진(077970): 4375
- `market_regime_prior_observed` 에스엘(005850): 4236
- `swing_entry_micro_context_observed` 에스엘(005850): 4235

## OFI/QI Micro Context

- sample_count: `46863`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.0295`
- stale_missing_reason_counts: `{'micro_missing': 1383, 'micro_not_ready': 226, 'state_insufficient': 226}`
- stale_missing_reason_combination_counts: `{'micro_missing': 1157, 'micro_missing+micro_not_ready+state_insufficient': 226}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 5, 'micro_missing': 11}`
- stale_missing_group_counts: `{'exit': 1168, 'entry': 215}`
- stale_missing_group_unique_record_counts: `{'entry': 5, 'exit': 11}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 42130, 'bullish': 1569, 'bearish': 1718, 'insufficient': 215}`
- scale_in_micro_state_counts: `{'neutral': 45}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 1157, 'CONFIRM_EXIT': 10, 'DEBOUNCE_EXIT': 1}`
