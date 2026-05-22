# Swing Selection Funnel Report - 2026-05-22

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `15`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 113 | 11 |
| `blocked_swing_gap` | 58064 | 9 |
| `blocked_swing_score_vpw` | 80953 | 9 |
| `gatekeeper_fast_reuse_bypass` | 113 | 11 |
| `holding_flow_ofi_smoothing_applied` | 517 | 74 |
| `holding_started` | 6 | 1 |
| `swing_probe_discarded` | 3914 | 15 |
| `swing_probe_entry_candidate` | 18 | 12 |
| `swing_probe_exit_signal` | 18 | 14 |
| `swing_probe_holding_started` | 18 | 12 |
| `swing_probe_scale_in_order_assumed_filled` | 10 | 8 |
| `swing_probe_sell_order_assumed_filled` | 18 | 14 |
| `swing_reentry_counterfactual_after_loss` | 59 | 1 |
| `swing_same_symbol_loss_reentry_cooldown` | 1 | 1 |
| `swing_scale_in_micro_context_observed` | 10 | 8 |
| `swing_sim_scale_in_order_assumed_filled` | 10 | 8 |

## Top Code Stage

- `blocked_swing_score_vpw` 한국가스공사(036460): 14194
- `blocked_swing_score_vpw` 팬오션(028670): 14193
- `blocked_swing_score_vpw` 현대해상(001450): 14107
- `blocked_swing_gap` 삼성에스디에스(018260): 13876
- `blocked_swing_score_vpw` 삼성E&A(028050): 13786
- `blocked_swing_gap` 디아이씨(092200): 13416
- `blocked_swing_gap` 유한양행(000100): 13309
- `blocked_swing_score_vpw` 한화생명(088350): 9067
- `blocked_swing_score_vpw` 대한항공(003490): 8750
- `blocked_swing_gap` LG디스플레이(034220): 7390

## OFI/QI Micro Context

- sample_count: `565`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `0.915`
- stale_missing_reason_counts: `{'micro_missing': 517, 'micro_not_ready': 1, 'state_insufficient': 1}`
- stale_missing_reason_combination_counts: `{'micro_missing': 516, 'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'exit': 517}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'neutral': 27, 'bullish': 3}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 510, 'CONFIRM_EXIT': 7}`
