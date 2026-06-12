# Swing Selection Funnel Report - 2026-06-12

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `26`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 5193 | 24 |
| `blocked_swing_gap` | 2761 | 20 |
| `blocked_swing_score_vpw` | 5198 | 23 |
| `gatekeeper_fast_reuse` | 62 | 12 |
| `gatekeeper_fast_reuse_bypass` | 5133 | 24 |
| `gatekeeper_reject_cache_reuse` | 3181 | 24 |
| `holding_flow_ofi_smoothing_applied` | 274 | 95 |
| `holding_started` | 31 | 1 |
| `market_regime_prior_observed` | 10392 | 26 |
| `swing_entry_micro_context_observed` | 10388 | 26 |
| `swing_probe_discarded` | 4645 | 16 |
| `swing_probe_entry_candidate` | 9 | 8 |
| `swing_probe_exit_signal` | 9 | 9 |
| `swing_probe_holding_started` | 9 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 7 | 7 |
| `swing_probe_sell_order_assumed_filled` | 9 | 9 |
| `swing_reentry_counterfactual_after_loss` | 16 | 3 |
| `swing_same_symbol_loss_reentry_blocked` | 4 | 3 |
| `swing_same_symbol_loss_reentry_cooldown` | 6 | 5 |
| `swing_scale_in_micro_context_observed` | 330 | 18 |
| `swing_sim_buy_order_assumed_filled` | 74 | 26 |
| `swing_sim_holding_started` | 74 | 26 |
| `swing_sim_order_bundle_assumed_filled` | 74 | 26 |
| `swing_sim_scale_in_order_assumed_filled` | 26 | 16 |
| `swing_sim_sell_order_assumed_filled` | 4 | 3 |

## Top Code Stage

- `swing_probe_discarded` NH투자증권(005940): 849
- `swing_probe_discarded` 우리금융지주(316140): 802
- `swing_probe_discarded` 아모레퍼시픽홀딩스(002790): 656
- `swing_probe_discarded` 한국가스공사(036460): 655
- `market_regime_prior_observed` 롯데리츠(330590): 648
- `swing_entry_micro_context_observed` 롯데리츠(330590): 648
- `market_regime_prior_observed` 넷마블(251270): 645
- `swing_entry_micro_context_observed` 넷마블(251270): 645
- `blocked_swing_score_vpw` 카카오페이(377300): 644
- `market_regime_prior_observed` 카카오페이(377300): 644

## OFI/QI Micro Context

- sample_count: `21582`
- stale_missing_unique_record_count: `28`
- stale_missing_ratio: `0.5685`
- stale_missing_reason_counts: `{'micro_missing': 12269, 'micro_not_ready': 12000, 'state_insufficient': 12000, 'observer_unhealthy': 22}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 11978, 'micro_missing': 269, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 22}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'entry': 11832, 'exit': 274, 'scale_in': 163}`
- stale_missing_group_unique_record_counts: `{'entry': 23, 'scale_in': 2, 'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 22, 'observer_unhealthy_with_other_reason': 22, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 8485, 'bearish': 394, 'bullish': 221, 'insufficient': 11832}`
- scale_in_micro_state_counts: `{'neutral': 187, 'insufficient': 163, 'bullish': 9, 'bearish': 4}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 274}`
