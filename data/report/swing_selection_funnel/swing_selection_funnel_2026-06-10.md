# Swing Selection Funnel Report - 2026-06-10

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `28`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 2769 | 20 |
| `blocked_swing_gap` | 963 | 4 |
| `blocked_swing_score_vpw` | 15322 | 27 |
| `gatekeeper_fast_reuse` | 177 | 5 |
| `gatekeeper_fast_reuse_bypass` | 2596 | 20 |
| `gatekeeper_reject_cache_reuse` | 2005 | 11 |
| `holding_flow_ofi_smoothing_applied` | 899 | 104 |
| `market_regime_block` | 16182 | 28 |
| `market_regime_prior_observed` | 1909 | 28 |
| `swing_entry_micro_context_observed` | 17895 | 24 |
| `swing_probe_discarded` | 5017 | 20 |
| `swing_probe_entry_candidate` | 11 | 8 |
| `swing_probe_exit_signal` | 11 | 10 |
| `swing_probe_holding_started` | 11 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 7 | 7 |
| `swing_probe_sell_order_assumed_filled` | 11 | 10 |
| `swing_reentry_counterfactual_after_loss` | 64 | 5 |
| `swing_same_symbol_loss_reentry_blocked` | 18 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 14 | 10 |
| `swing_scale_in_micro_context_observed` | 47 | 19 |
| `swing_sim_buy_order_assumed_filled` | 74 | 22 |
| `swing_sim_holding_started` | 74 | 22 |
| `swing_sim_order_bundle_assumed_filled` | 74 | 22 |
| `swing_sim_scale_in_order_assumed_filled` | 34 | 18 |
| `swing_sim_sell_order_assumed_filled` | 8 | 4 |

## Top Code Stage

- `swing_entry_micro_context_observed` 카카오(035720): 1707
- `blocked_swing_score_vpw` 카카오(035720): 1705
- `swing_entry_micro_context_observed` 팬오션(028670): 1671
- `blocked_swing_score_vpw` GS(078930): 1669
- `swing_entry_micro_context_observed` GS(078930): 1669
- `blocked_swing_score_vpw` 한화생명(088350): 1669
- `swing_entry_micro_context_observed` 한화생명(088350): 1669
- `blocked_swing_score_vpw` 팬오션(028670): 1666
- `swing_entry_micro_context_observed` 넷마블(251270): 1659
- `swing_entry_micro_context_observed` 아모레퍼시픽홀딩스(002790): 1659

## OFI/QI Micro Context

- sample_count: `37158`
- stale_missing_unique_record_count: `36`
- stale_missing_ratio: `0.0945`
- stale_missing_reason_counts: `{'micro_missing': 3510, 'micro_not_ready': 2626, 'state_insufficient': 2626, 'observer_unhealthy': 16}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2610, 'micro_missing': 884, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 9, 'micro_missing': 9}`
- stale_missing_group_counts: `{'entry': 2608, 'exit': 900, 'scale_in': 2}`
- stale_missing_group_unique_record_counts: `{'entry': 26, 'exit': 10, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 16, 'observer_unhealthy_with_other_reason': 16, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'neutral': 31327, 'bearish': 862, 'bullish': 1355, 'insufficient': 2608}`
- scale_in_micro_state_counts: `{'bearish': 8, 'neutral': 77, 'bullish': 1, 'insufficient': 2}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 898, 'CONFIRM_EXIT': 1}`
