# Swing Selection Funnel Report - 2026-06-23

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `2`
- fallback_written_to_recommendations: `False`
- csv_rows: `2`
- db_rows: `6`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 87 | 3 |
| `blocked_swing_gap` | 184 | 1 |
| `blocked_swing_score_vpw` | 1996 | 6 |
| `gatekeeper_fast_reuse` | 1 | 1 |
| `gatekeeper_fast_reuse_bypass` | 86 | 3 |
| `gatekeeper_reject_cache_reuse` | 52 | 3 |
| `holding_flow_ofi_smoothing_applied` | 124 | 35 |
| `market_regime_block` | 1921 | 6 |
| `market_regime_prior_observed` | 162 | 6 |
| `swing_entry_micro_context_observed` | 2052 | 6 |
| `swing_probe_discarded` | 2549 | 6 |
| `swing_probe_entry_candidate` | 13 | 6 |
| `swing_probe_exit_signal` | 12 | 9 |
| `swing_probe_holding_started` | 13 | 6 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 8 |
| `swing_probe_sell_order_assumed_filled` | 12 | 9 |
| `swing_reentry_counterfactual_after_loss` | 94 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 31 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 8 |
| `swing_scale_in_micro_context_observed` | 15 | 8 |
| `swing_sim_buy_order_assumed_filled` | 43 | 4 |
| `swing_sim_holding_started` | 43 | 4 |
| `swing_sim_order_bundle_assumed_filled` | 43 | 4 |
| `swing_sim_scale_in_order_assumed_filled` | 12 | 8 |

## Top Code Stage

- `swing_probe_discarded` 대상(001680): 560
- `swing_probe_discarded` 코오롱인더(120110): 551
- `swing_probe_discarded` 에스엘(005850): 516
- `blocked_swing_score_vpw` 에스엘(005850): 486
- `swing_entry_micro_context_observed` 에스엘(005850): 479
- `blocked_swing_score_vpw` 대상(001680): 476
- `swing_entry_micro_context_observed` 대상(001680): 476
- `market_regime_block` 에스엘(005850): 459
- `market_regime_block` 대상(001680): 449
- `swing_entry_micro_context_observed` 코오롱인더(120110): 428

## OFI/QI Micro Context

- sample_count: `4427`
- stale_missing_unique_record_count: `8`
- stale_missing_ratio: `0.8581`
- stale_missing_reason_counts: `{'micro_missing': 3799, 'micro_not_ready': 3676, 'state_insufficient': 3676, 'observer_unhealthy': 216}`
- stale_missing_reason_combination_counts: `{'micro_missing': 123, 'micro_missing+micro_not_ready+state_insufficient': 3460, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 216}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 8, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'exit': 129, 'entry': 3664, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'entry': 6, 'scale_in': 2, 'exit': 5}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 216, 'observer_unhealthy_with_other_reason': 216, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 555, 'bearish': 22, 'bullish': 11, 'insufficient': 3664}`
- scale_in_micro_state_counts: `{'neutral': 29, 'bullish': 1, 'insufficient': 6, 'bearish': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 123, 'CONFIRM_EXIT': 1}`
