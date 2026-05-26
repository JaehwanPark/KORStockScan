# Swing Selection Funnel Report - 2026-05-26

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `22`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 33 | 6 |
| `blocked_swing_gap` | 13766 | 5 |
| `blocked_swing_score_vpw` | 187457 | 22 |
| `gatekeeper_fast_reuse_bypass` | 33 | 6 |
| `holding_flow_ofi_smoothing_applied` | 794 | 97 |
| `holding_started` | 7 | 1 |
| `swing_probe_discarded` | 8029 | 22 |
| `swing_probe_entry_candidate` | 30 | 13 |
| `swing_probe_exit_signal` | 21 | 9 |
| `swing_probe_holding_started` | 30 | 13 |
| `swing_probe_scale_in_order_assumed_filled` | 19 | 13 |
| `swing_probe_sell_order_assumed_filled` | 21 | 9 |
| `swing_reentry_counterfactual_after_loss` | 528 | 5 |
| `swing_same_symbol_loss_reentry_cooldown` | 10 | 5 |
| `swing_scale_in_micro_context_observed` | 19 | 13 |
| `swing_sim_scale_in_order_assumed_filled` | 19 | 13 |

## Top Code Stage

- `blocked_swing_score_vpw` KB금융(105560): 10444
- `blocked_swing_score_vpw` GS리테일(007070): 10444
- `blocked_swing_score_vpw` NC(036570): 10444
- `blocked_swing_score_vpw` 한국타이어앤테크놀로지(161390): 10444
- `blocked_swing_score_vpw` 셀트리온(068270): 10444
- `blocked_swing_score_vpw` KT&G(033780): 10443
- `blocked_swing_score_vpw` 현대해상(001450): 10443
- `blocked_swing_score_vpw` GS(078930): 10442
- `blocked_swing_score_vpw` HMM(011200): 10442
- `blocked_swing_score_vpw` 한세실업(105630): 10442

## OFI/QI Micro Context

- sample_count: `872`
- stale_missing_unique_record_count: `7`
- stale_missing_ratio: `0.9117`
- stale_missing_reason_counts: `{'micro_missing': 795, 'observer_unhealthy': 1, 'micro_not_ready': 4, 'state_insufficient': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing': 791, 'micro_missing+micro_not_ready+state_insufficient': 3}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing': 6}`
- stale_missing_group_counts: `{'exit': 795}`
- stale_missing_group_unique_record_counts: `{'exit': 7}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 57}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 773, 'CONFIRM_EXIT': 12, 'DEBOUNCE_EXIT': 9}`
