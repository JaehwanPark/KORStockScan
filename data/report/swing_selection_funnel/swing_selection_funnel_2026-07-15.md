# Swing Selection Funnel Report - 2026-07-15

- owner: `SwingModelSelectionFunnelRepair`
- selection_mode: `SELECTED`
- selected_count: `2`
- fallback_written_to_recommendations: `False`
- csv_rows: `2`
- db_rows: `0`
- db_load_gap: `False`
- db_load_skip_reason: `swing_real_watching_disabled_by_policy`
- entered_rows: `0`
- submitted_unique_records: `0`

## Pipeline Raw vs Unique

| stage | raw | unique_records |
| --- | ---: | ---: |
| `holding_flow_ofi_smoothing_applied` | 14 | 4 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` KB금융(105560): 9
- `holding_flow_ofi_smoothing_applied` 대우건설(047040): 2
- `holding_flow_ofi_smoothing_applied` 신일전자(002700): 2
- `holding_flow_ofi_smoothing_applied` 브이엠(089970): 1

## OFI/QI Micro Context

- sample_count: `14`
- stale_missing_unique_record_count: `3`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 14}`
- stale_missing_reason_combination_counts: `{'micro_missing': 14}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 3}`
- stale_missing_group_counts: `{'exit': 14}`
- stale_missing_group_unique_record_counts: `{'exit': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 14}`
