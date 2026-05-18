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
| `blocked_gatekeeper_reject` | 140 | 20 |
| `blocked_swing_gap` | 96353 | 8 |
| `blocked_swing_score_vpw` | 550610 | 39 |
| `gatekeeper_fast_reuse_bypass` | 140 | 20 |
| `holding_flow_ofi_smoothing_applied` | 62 | 2 |
| `swing_probe_discarded` | 14749 | 42 |
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

- `blocked_swing_score_vpw` 한온시스템(018880): 19335
- `blocked_swing_score_vpw` LG디스플레이(034220): 19330
- `blocked_swing_gap` 에이치브이엠(295310): 19328
- `blocked_swing_score_vpw` HL만도(204320): 19308
- `blocked_swing_score_vpw` 한올바이오파마(009420): 19279
- `blocked_swing_score_vpw` 한미약품(128940): 19258
- `blocked_swing_score_vpw` 한화(000880): 19258
- `blocked_swing_score_vpw` 팬오션(028670): 19226
- `blocked_swing_score_vpw` iM금융지주(139130): 19132
- `blocked_swing_score_vpw` 삼성에스디에스(018260): 19096

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
