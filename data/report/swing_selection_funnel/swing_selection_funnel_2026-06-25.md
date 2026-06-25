# Swing Selection Funnel Report - 2026-06-25

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `3`
- fallback_written_to_recommendations: `False`
- csv_rows: `3`
- db_rows: `0`
- db_load_gap: `False`
- db_load_skip_reason: `swing_real_watching_disabled_by_policy`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `holding_flow_ofi_smoothing_applied` | 34 | 15 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 삼화콘덴서(001820): 6
- `holding_flow_ofi_smoothing_applied` 마녀공장(439090): 6
- `holding_flow_ofi_smoothing_applied` SK하이닉스(000660): 5
- `holding_flow_ofi_smoothing_applied` 대명에너지(389260): 3
- `holding_flow_ofi_smoothing_applied` 테스(095610): 2
- `holding_flow_ofi_smoothing_applied` 로킷헬스케어(376900): 2
- `holding_flow_ofi_smoothing_applied` 한올바이오파마(009420): 2
- `holding_flow_ofi_smoothing_applied` 한화오션(042660): 1
- `holding_flow_ofi_smoothing_applied` 한미반도체(042700): 1
- `holding_flow_ofi_smoothing_applied` 디앤디파마텍(347850): 1

## OFI/QI Micro Context

- sample_count: `34`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 34, 'micro_not_ready': 2, 'state_insufficient': 2}`
- stale_missing_reason_combination_counts: `{'micro_missing': 32, 'micro_missing+micro_not_ready+state_insufficient': 2}`
- stale_missing_reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'exit': 34}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 33, 'CONFIRM_EXIT': 1}`
