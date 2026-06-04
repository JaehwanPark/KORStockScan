# Swing Selection Funnel Report - 2026-06-04

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `14`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 829 | 3 |
| `blocked_swing_gap` | 838 | 5 |
| `blocked_swing_score_vpw` | 3591 | 12 |
| `gatekeeper_fast_reuse` | 12 | 1 |
| `gatekeeper_fast_reuse_bypass` | 818 | 3 |
| `gatekeeper_reject_cache_reuse` | 768 | 3 |
| `holding_flow_ofi_smoothing_applied` | 52 | 18 |
| `market_regime_prior_observed` | 4420 | 14 |
| `swing_entry_micro_context_observed` | 4401 | 11 |
| `swing_probe_discarded` | 806 | 14 |
| `swing_reentry_counterfactual_after_loss` | 8 | 1 |
| `swing_same_symbol_loss_reentry_blocked` | 2 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_scale_in_micro_context_observed` | 6 | 5 |
| `swing_sim_buy_order_assumed_filled` | 17 | 11 |
| `swing_sim_holding_started` | 17 | 11 |
| `swing_sim_order_bundle_assumed_filled` | 17 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 6 | 5 |
| `swing_sim_sell_order_assumed_filled` | 3 | 2 |

## Top Code Stage

- `blocked_swing_score_vpw` 포스코DX(022100): 875
- `market_regime_prior_observed` 포스코DX(022100): 875
- `swing_entry_micro_context_observed` 포스코DX(022100): 875
- `blocked_swing_score_vpw` 한올바이오파마(009420): 837
- `market_regime_prior_observed` 한올바이오파마(009420): 837
- `swing_entry_micro_context_observed` 한올바이오파마(009420): 837
- `blocked_swing_score_vpw` 삼성E&A(028050): 822
- `market_regime_prior_observed` 삼성E&A(028050): 822
- `swing_entry_micro_context_observed` 삼성E&A(028050): 822
- `blocked_gatekeeper_reject` 한국앤컴퍼니(000240): 819

## OFI/QI Micro Context

- sample_count: `8924`
- stale_missing_unique_record_count: `14`
- stale_missing_ratio: `0.0196`
- stale_missing_reason_counts: `{'micro_missing': 175, 'observer_unhealthy': 8, 'micro_not_ready': 124, 'state_insufficient': 124}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 116, 'micro_missing': 51}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing': 1}`
- stale_missing_group_counts: `{'entry': 123, 'exit': 52}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'insufficient': 123, 'neutral': 8241, 'bearish': 287, 'bullish': 206}`
- scale_in_micro_state_counts: `{'neutral': 12}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 52}`
