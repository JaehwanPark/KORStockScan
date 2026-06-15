# Swing Selection Funnel Report - 2026-06-15

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `17`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 9920 | 15 |
| `blocked_swing_gap` | 9200 | 11 |
| `blocked_swing_score_vpw` | 6084 | 14 |
| `gatekeeper_fast_reuse` | 844 | 12 |
| `gatekeeper_fast_reuse_bypass` | 9083 | 15 |
| `gatekeeper_reject_cache_reuse` | 7633 | 15 |
| `holding_flow_ofi_smoothing_applied` | 217 | 71 |
| `holding_started` | 2 | 1 |
| `market_regime_prior_observed` | 16009 | 17 |
| `swing_entry_micro_context_observed` | 16009 | 17 |
| `swing_probe_discarded` | 1619 | 11 |
| `swing_probe_entry_candidate` | 4 | 4 |
| `swing_probe_exit_signal` | 4 | 4 |
| `swing_probe_holding_started` | 4 | 4 |
| `swing_probe_scale_in_order_assumed_filled` | 3 | 3 |
| `swing_probe_sell_order_assumed_filled` | 4 | 4 |
| `swing_scale_in_micro_context_observed` | 595 | 9 |
| `swing_sim_buy_order_assumed_filled` | 69 | 17 |
| `swing_sim_holding_started` | 69 | 17 |
| `swing_sim_order_bundle_assumed_filled` | 69 | 17 |
| `swing_sim_scale_in_order_assumed_filled` | 16 | 8 |
| `swing_sim_sell_order_assumed_filled` | 3 | 2 |

## Top Code Stage

- `market_regime_prior_observed` LX세미콘(108320): 1919
- `swing_entry_micro_context_observed` LX세미콘(108320): 1919
- `market_regime_prior_observed` 일진홀딩스(015860): 1917
- `swing_entry_micro_context_observed` 일진홀딩스(015860): 1917
- `market_regime_prior_observed` 미스토홀딩스(081660): 1916
- `swing_entry_micro_context_observed` 미스토홀딩스(081660): 1916
- `blocked_swing_score_vpw` 미스토홀딩스(081660): 1868
- `market_regime_prior_observed` 카카오뱅크(323410): 1813
- `swing_entry_micro_context_observed` 카카오뱅크(323410): 1813
- `blocked_swing_gap` 일진홀딩스(015860): 1779

## OFI/QI Micro Context

- sample_count: `32994`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.2009`
- stale_missing_reason_counts: `{'micro_missing': 6628, 'micro_not_ready': 6413, 'state_insufficient': 6413, 'observer_unhealthy': 18}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 6395, 'micro_missing': 215, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'entry': 6404, 'exit': 217, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{'bearish': 983, 'neutral': 23981, 'bullish': 788, 'insufficient': 6404}`
- scale_in_micro_state_counts: `{'insufficient': 7, 'bullish': 19, 'neutral': 569, 'bearish': 19}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 216, 'CONFIRM_EXIT': 1}`
