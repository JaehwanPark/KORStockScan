# Swing Selection Funnel Report - 2026-05-21

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `24`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 143 | 19 |
| `blocked_swing_gap` | 119651 | 17 |
| `blocked_swing_score_vpw` | 134755 | 18 |
| `gatekeeper_fast_reuse_bypass` | 143 | 19 |
| `holding_flow_ofi_smoothing_applied` | 732 | 85 |
| `holding_started` | 11 | 1 |
| `swing_probe_discarded` | 7872 | 24 |
| `swing_probe_entry_candidate` | 10 | 8 |
| `swing_probe_exit_signal` | 9 | 9 |
| `swing_probe_holding_started` | 10 | 8 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 8 |
| `swing_probe_sell_order_assumed_filled` | 9 | 9 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_scale_in_micro_context_observed` | 9 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 9 | 8 |

## Top Code Stage

- `blocked_swing_score_vpw` GS(078930): 14448
- `blocked_swing_gap` 한국항공우주(047810): 13340
- `blocked_swing_gap` 셀트리온(068270): 13198
- `blocked_swing_score_vpw` 기업은행(024110): 13197
- `blocked_swing_score_vpw` 하이브(352820): 12161
- `blocked_swing_score_vpw` 한화에어로스페이스(012450): 12068
- `blocked_swing_gap` 대한항공(003490): 12059
- `blocked_swing_gap` LG씨엔에스(064400): 11951
- `blocked_swing_score_vpw` KB금융(105560): 11834
- `blocked_swing_score_vpw` BNK금융지주(138930): 10568

## OFI/QI Micro Context

- sample_count: `768`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.957`
- stale_missing_reason_counts: `{'micro_missing': 735, 'micro_not_ready': 6, 'state_insufficient': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing': 729, 'micro_missing+micro_not_ready+state_insufficient': 6}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1, 'micro_missing': 1}`
- stale_missing_group_counts: `{'exit': 732, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 24, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 717, 'CONFIRM_EXIT': 15}`
