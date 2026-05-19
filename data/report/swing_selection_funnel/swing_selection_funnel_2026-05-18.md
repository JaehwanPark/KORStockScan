# Swing Selection Funnel Report - 2026-05-18

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `42`
- db_load_gap: `False`
- db_load_skip_reason: `loaded`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `blocked_gatekeeper_reject` | 154 | 20 |
| `blocked_swing_gap` | 139697 | 8 |
| `blocked_swing_score_vpw` | 666194 | 39 |
| `gatekeeper_fast_reuse_bypass` | 154 | 20 |
| `holding_flow_ofi_smoothing_applied` | 62 | 2 |
| `holding_started` | 1 | 1 |
| `swing_probe_discarded` | 17469 | 42 |
| `swing_probe_entry_candidate` | 38 | 21 |
| `swing_probe_exit_signal` | 38 | 28 |
| `swing_probe_holding_started` | 38 | 21 |
| `swing_probe_scale_in_order_assumed_filled` | 19 | 16 |
| `swing_probe_sell_order_assumed_filled` | 38 | 28 |
| `swing_reentry_counterfactual_after_loss` | 453 | 10 |
| `swing_same_symbol_loss_reentry_cooldown` | 13 | 13 |
| `swing_scale_in_micro_context_observed` | 20 | 17 |
| `swing_sim_scale_in_order_assumed_filled` | 19 | 16 |

## Top Code Stage

- `blocked_swing_score_vpw` 한온시스템(018880): 26559
- `blocked_swing_score_vpw` LG디스플레이(034220): 26554
- `blocked_swing_gap` 에이치브이엠(295310): 26552
- `blocked_swing_score_vpw` HL만도(204320): 26532
- `blocked_swing_score_vpw` 한올바이오파마(009420): 26503
- `blocked_swing_score_vpw` 한미약품(128940): 26482
- `blocked_swing_score_vpw` 한화(000880): 26482
- `blocked_swing_score_vpw` 팬오션(028670): 26450
- `blocked_swing_score_vpw` iM금융지주(139130): 26356
- `blocked_swing_score_vpw` 삼성에스디에스(018260): 26320

## OFI/QI Micro Context

- sample_count: `158`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.4304`
- stale_missing_reason_counts: `{'micro_missing': 68, 'observer_unhealthy': 6, 'micro_not_ready': 6, 'state_insufficient': 6}`
- stale_missing_reason_combination_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6, 'micro_missing': 62}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'scale_in': 6, 'exit': 62}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{'insufficient': 6, 'neutral': 52}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 62}`
