# Swing Selection Funnel Report - 2026-06-17

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
| `blocked_gatekeeper_reject` | 8769 | 10 |
| `blocked_swing_gap` | 2104 | 4 |
| `blocked_swing_score_vpw` | 35987 | 16 |
| `gatekeeper_fast_reuse` | 738 | 6 |
| `gatekeeper_fast_reuse_bypass` | 8031 | 10 |
| `gatekeeper_reject_cache_reuse` | 7402 | 10 |
| `holding_flow_ofi_smoothing_applied` | 369 | 109 |
| `market_regime_pass` | 44756 | 16 |
| `swing_entry_micro_context_observed` | 44754 | 16 |
| `swing_probe_discarded` | 2860 | 12 |
| `swing_probe_entry_candidate` | 3 | 3 |
| `swing_probe_exit_signal` | 3 | 3 |
| `swing_probe_holding_started` | 3 | 3 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 3 | 3 |
| `swing_reentry_counterfactual_after_loss` | 6 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 2 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 3 |
| `swing_scale_in_micro_context_observed` | 62 | 7 |
| `swing_sim_buy_order_assumed_filled` | 31 | 16 |
| `swing_sim_holding_started` | 31 | 16 |
| `swing_sim_order_bundle_assumed_filled` | 31 | 16 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 7 |
| `swing_sim_sell_order_assumed_filled` | 3 | 3 |

## Top Code Stage

- `blocked_swing_score_vpw` 카카오뱅크(323410): 4077
- `market_regime_pass` 카카오뱅크(323410): 4077
- `swing_entry_micro_context_observed` 카카오뱅크(323410): 4077
- `market_regime_pass` 코웨이(021240): 4077
- `swing_entry_micro_context_observed` 코웨이(021240): 4077
- `market_regime_pass` 한국가스공사(036460): 4076
- `swing_entry_micro_context_observed` 한국가스공사(036460): 4076
- `market_regime_pass` 미스토홀딩스(081660): 4076
- `swing_entry_micro_context_observed` 미스토홀딩스(081660): 4076
- `blocked_swing_score_vpw` 에스엘(005850): 4076

## OFI/QI Micro Context

- sample_count: `90023`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.1407`
- stale_missing_reason_counts: `{'micro_missing': 12670, 'micro_not_ready': 12312, 'state_insufficient': 12312, 'observer_unhealthy': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 12308, 'micro_missing': 358, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'entry': 12294, 'exit': 369, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 72604, 'bullish': 2645, 'insufficient': 12294, 'bearish': 2029}`
- scale_in_micro_state_counts: `{'neutral': 63, 'bearish': 5, 'insufficient': 7, 'bullish': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 368, 'CONFIRM_EXIT': 1}`
