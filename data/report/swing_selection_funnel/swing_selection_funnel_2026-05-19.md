# Swing Selection Funnel Report - 2026-05-19

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `20`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 39 | 8 |
| `blocked_swing_gap` | 14396 | 2 |
| `blocked_swing_score_vpw` | 251919 | 20 |
| `gatekeeper_fast_reuse_bypass` | 39 | 8 |
| `holding_flow_ofi_smoothing_applied` | 463 | 50 |
| `swing_probe_discarded` | 7359 | 20 |
| `swing_probe_entry_candidate` | 13 | 11 |
| `swing_probe_exit_signal` | 14 | 14 |
| `swing_probe_holding_started` | 13 | 11 |
| `swing_probe_scale_in_order_assumed_filled` | 11 | 11 |
| `swing_probe_sell_order_assumed_filled` | 14 | 14 |
| `swing_reentry_counterfactual_after_loss` | 388 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 9 | 9 |
| `swing_scale_in_micro_context_observed` | 11 | 11 |
| `swing_sim_scale_in_order_assumed_filled` | 11 | 11 |

## Top Code Stage

- `blocked_swing_score_vpw` 삼성물산(028260): 15648
- `blocked_swing_score_vpw` 기아(000270): 15647
- `blocked_swing_score_vpw` LG디스플레이(034220): 15647
- `blocked_swing_score_vpw` SK아이이테크놀로지(361610): 15647
- `blocked_swing_score_vpw` 현대글로비스(086280): 15646
- `blocked_swing_score_vpw` 에스엘(005850): 15646
- `blocked_swing_score_vpw` HL만도(204320): 15646
- `blocked_swing_score_vpw` 현대위아(011210): 15645
- `blocked_swing_score_vpw` 삼성에스디에스(018260): 15645
- `blocked_swing_score_vpw` 현대제철(004020): 15645

## OFI/QI Micro Context

- sample_count: `510`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.9216`
- stale_missing_reason_counts: `{'micro_missing': 470, 'micro_not_ready': 24, 'state_insufficient': 24, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 467, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'exit': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 27, 'bullish': 3, 'insufficient': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 456, 'CONFIRM_EXIT': 7}`
