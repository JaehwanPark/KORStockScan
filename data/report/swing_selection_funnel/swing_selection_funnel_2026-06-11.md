# Swing Selection Funnel Report - 2026-06-11

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `2`
- fallback_written_to_recommendations: `False`
- csv_rows: `2`
- db_rows: `31`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2782 | 22 |
| `blocked_swing_gap` | 1169 | 12 |
| `blocked_swing_score_vpw` | 6025 | 27 |
| `gatekeeper_fast_reuse` | 31 | 9 |
| `gatekeeper_fast_reuse_bypass` | 2752 | 22 |
| `gatekeeper_reject_cache_reuse` | 1229 | 17 |
| `holding_flow_ofi_smoothing_applied` | 461 | 107 |
| `market_regime_block` | 1225 | 31 |
| `market_regime_prior_observed` | 7582 | 31 |
| `swing_entry_micro_context_observed` | 8770 | 31 |
| `swing_probe_discarded` | 5449 | 19 |
| `swing_probe_entry_candidate` | 19 | 10 |
| `swing_probe_exit_signal` | 19 | 14 |
| `swing_probe_holding_started` | 19 | 10 |
| `swing_probe_scale_in_order_assumed_filled` | 12 | 7 |
| `swing_probe_sell_order_assumed_filled` | 19 | 14 |
| `swing_reentry_counterfactual_after_loss` | 32 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 8 | 4 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 7 |
| `swing_scale_in_micro_context_observed` | 36 | 13 |
| `swing_sim_buy_order_assumed_filled` | 57 | 30 |
| `swing_sim_holding_started` | 57 | 30 |
| `swing_sim_order_bundle_assumed_filled` | 57 | 30 |
| `swing_sim_scale_in_order_assumed_filled` | 22 | 12 |
| `swing_sim_sell_order_assumed_filled` | 10 | 5 |

## Top Code Stage

- `swing_probe_discarded` 코웨이(021240): 695
- `swing_probe_discarded` 호텔신라(008770): 695
- `swing_probe_discarded` 기업은행(024110): 690
- `swing_probe_discarded` HD현대중공업(329180): 648
- `swing_probe_discarded` JB금융지주(175330): 629
- `swing_probe_discarded` 한국타이어앤테크놀로지(161390): 595
- `swing_probe_discarded` HJ중공업(097230): 429
- `swing_entry_micro_context_observed` 코웨이(021240): 414
- `swing_entry_micro_context_observed` 호텔신라(008770): 414
- `swing_entry_micro_context_observed` JB금융지주(175330): 414

## OFI/QI Micro Context

- sample_count: `18261`
- stale_missing_unique_record_count: `17`
- stale_missing_ratio: `0.0714`
- stale_missing_reason_counts: `{'micro_missing': 1303, 'observer_unhealthy': 3, 'micro_not_ready': 845, 'state_insufficient': 845}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3, 'micro_missing+micro_not_ready+state_insufficient': 842, 'micro_missing': 458}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing': 2}`
- stale_missing_group_counts: `{'scale_in': 3, 'entry': 839, 'exit': 461}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'entry': 14, 'exit': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 15795, 'bearish': 625, 'bullish': 442, 'insufficient': 839}`
- scale_in_micro_state_counts: `{'insufficient': 3, 'neutral': 66, 'bearish': 1}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 461}`
