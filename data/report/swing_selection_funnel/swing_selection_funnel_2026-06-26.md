# Swing Selection Funnel Report - 2026-06-26

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
| `holding_flow_ofi_smoothing_applied` | 37 | 14 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 대명에너지(389260): 10
- `holding_flow_ofi_smoothing_applied` 로킷헬스케어(376900): 7
- `holding_flow_ofi_smoothing_applied` 원익IPS(240810): 4
- `holding_flow_ofi_smoothing_applied` 엠로(058970): 3
- `holding_flow_ofi_smoothing_applied` SKC(011790): 2
- `holding_flow_ofi_smoothing_applied` 키스트론(475430): 2
- `holding_flow_ofi_smoothing_applied` 일신방직(003200): 2
- `holding_flow_ofi_smoothing_applied` 삼성SDI(006400): 1
- `holding_flow_ofi_smoothing_applied` 피에스케이(319660): 1
- `holding_flow_ofi_smoothing_applied` 마키나락스(477850): 1

## OFI/QI Micro Context

- sample_count: `37`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 37, 'micro_not_ready': 4, 'state_insufficient': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing': 33, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 1}`
- stale_missing_group_counts: `{'exit': 37}`
- stale_missing_group_unique_record_counts: `{'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 37}`
