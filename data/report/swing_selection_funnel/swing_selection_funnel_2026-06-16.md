# Swing Selection Funnel Report - 2026-06-16

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
| `blocked_gatekeeper_reject` | 9422 | 15 |
| `blocked_swing_gap` | 2171 | 10 |
| `blocked_swing_score_vpw` | 11285 | 18 |
| `gatekeeper_fast_reuse` | 636 | 11 |
| `gatekeeper_fast_reuse_bypass` | 8790 | 15 |
| `gatekeeper_reject_cache_reuse` | 7383 | 15 |
| `holding_flow_ofi_smoothing_applied` | 283 | 86 |
| `market_regime_pass` | 5239 | 21 |
| `market_regime_prior_observed` | 15469 | 21 |
| `swing_entry_micro_context_observed` | 20702 | 21 |
| `swing_probe_discarded` | 4064 | 17 |
| `swing_probe_entry_candidate` | 5 | 4 |
| `swing_probe_exit_signal` | 5 | 4 |
| `swing_probe_holding_started` | 5 | 4 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 5 | 4 |
| `swing_reentry_counterfactual_after_loss` | 17 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 6 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 3 | 2 |
| `swing_scale_in_micro_context_observed` | 703 | 11 |
| `swing_sim_buy_order_assumed_filled` | 79 | 21 |
| `swing_sim_holding_started` | 79 | 21 |
| `swing_sim_order_bundle_assumed_filled` | 79 | 21 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 8 |
| `swing_sim_sell_order_assumed_filled` | 5 | 3 |

## Top Code Stage

- `swing_entry_micro_context_observed` 현대엘리베이터(017800): 1913
- `blocked_swing_score_vpw` 대동(000490): 1913
- `swing_entry_micro_context_observed` 대동(000490): 1913
- `swing_entry_micro_context_observed` 롯데지주(004990): 1908
- `blocked_swing_score_vpw` HJ중공업(097230): 1908
- `swing_entry_micro_context_observed` HJ중공업(097230): 1908
- `blocked_swing_score_vpw` 코스모신소재(005070): 1908
- `swing_entry_micro_context_observed` 코스모신소재(005070): 1908
- `blocked_swing_score_vpw` 명신산업(009900): 1908
- `swing_entry_micro_context_observed` 명신산업(009900): 1908

## OFI/QI Micro Context

- sample_count: `42582`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `0.1875`
- stale_missing_reason_counts: `{'micro_missing': 7983, 'micro_not_ready': 7701, 'state_insufficient': 7701, 'observer_unhealthy': 25}`
- stale_missing_reason_combination_counts: `{'micro_missing': 282, 'micro_missing+micro_not_ready+state_insufficient': 7676, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 25}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'exit': 283, 'entry': 7700}`
- stale_missing_group_unique_record_counts: `{'entry': 18}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 25, 'observer_unhealthy_with_other_reason': 25, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 31600, 'bullish': 1023, 'bearish': 1250, 'insufficient': 7700}`
- scale_in_micro_state_counts: `{'bearish': 20, 'neutral': 672, 'bullish': 24}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 283}`
