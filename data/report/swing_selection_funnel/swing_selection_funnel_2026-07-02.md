# Swing Selection Funnel Report - 2026-07-02

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
| `holding_flow_ofi_smoothing_applied` | 25 | 10 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` LG전자(066570): 9
- `holding_flow_ofi_smoothing_applied` 삼성에스디에스(018260): 7
- `holding_flow_ofi_smoothing_applied` 계룡건설(013580): 2
- `holding_flow_ofi_smoothing_applied` 이수페타시스(007660): 1
- `holding_flow_ofi_smoothing_applied` 일진전기(103590): 1
- `holding_flow_ofi_smoothing_applied` 한화엔진(082740): 1
- `holding_flow_ofi_smoothing_applied` 강원에너지(114190): 1
- `holding_flow_ofi_smoothing_applied` 삼호개발(010960): 1
- `holding_flow_ofi_smoothing_applied` 특수건설(026150): 1
- `holding_flow_ofi_smoothing_applied` 삼성전자(005930): 1

## OFI/QI Micro Context

- sample_count: `25`
- stale_missing_unique_record_count: `4`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 25, 'micro_not_ready': 5, 'state_insufficient': 5}`
- stale_missing_reason_combination_counts: `{'micro_missing': 20, 'micro_missing+micro_not_ready+state_insufficient': 5}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 4, 'micro_missing+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 25}`
- stale_missing_group_unique_record_counts: `{'exit': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 25}`
