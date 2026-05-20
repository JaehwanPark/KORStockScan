# Swing Selection Funnel Report - 2026-05-20

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `25`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 87 | 9 |
| `blocked_swing_gap` | 416 | 1 |
| `blocked_swing_score_vpw` | 368504 | 25 |
| `gatekeeper_fast_reuse_bypass` | 87 | 9 |
| `holding_flow_ofi_smoothing_applied` | 630 | 67 |
| `holding_started` | 3 | 1 |
| `swing_probe_discarded` | 9216 | 25 |
| `swing_probe_entry_candidate` | 9 | 7 |
| `swing_probe_exit_signal` | 9 | 8 |
| `swing_probe_holding_started` | 9 | 7 |
| `swing_probe_scale_in_order_assumed_filled` | 9 | 8 |
| `swing_probe_sell_order_assumed_filled` | 9 | 8 |
| `swing_reentry_counterfactual_after_loss` | 204 | 6 |
| `swing_same_symbol_loss_reentry_cooldown` | 8 | 8 |
| `swing_scale_in_micro_context_observed` | 9 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 9 | 8 |

## Top Code Stage

- `blocked_swing_score_vpw` GS(078930): 18566
- `blocked_swing_score_vpw` 현대글로비스(086280): 18565
- `blocked_swing_score_vpw` 현대해상(001450): 18565
- `blocked_swing_score_vpw` LG디스플레이(034220): 18565
- `blocked_swing_score_vpw` 하이브(352820): 18565
- `blocked_swing_score_vpw` 대한항공(003490): 18564
- `blocked_swing_score_vpw` 강원랜드(035250): 18564
- `blocked_swing_score_vpw` BNK금융지주(138930): 18563
- `blocked_swing_score_vpw` 팬오션(028670): 18562
- `blocked_swing_score_vpw` HMM(011200): 18562

## OFI/QI Micro Context

- sample_count: `666`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.955`
- stale_missing_reason_counts: `{'micro_missing': 636, 'micro_not_ready': 20, 'state_insufficient': 20, 'observer_unhealthy': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 615, 'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy': 1}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'exit': 630, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 18, 'bearish': 3, 'insufficient': 6}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 619, 'CONFIRM_EXIT': 10, 'DEBOUNCE_EXIT': 1}`
