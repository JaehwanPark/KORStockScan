# Swing Selection Funnel Report - 2026-07-08

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
| `holding_flow_ofi_smoothing_applied` | 19 | 13 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 삼성에스디에스(018260): 6
- `holding_flow_ofi_smoothing_applied` 삼성전기(009150): 2
- `holding_flow_ofi_smoothing_applied` 네오팜(092730): 1
- `holding_flow_ofi_smoothing_applied` 금호타이어(073240): 1
- `holding_flow_ofi_smoothing_applied` 에이블씨엔씨(078520): 1
- `holding_flow_ofi_smoothing_applied` 한미사이언스(008930): 1
- `holding_flow_ofi_smoothing_applied` 한화오션(042660): 1
- `holding_flow_ofi_smoothing_applied` 레몬헬스케어(365660): 1
- `holding_flow_ofi_smoothing_applied` LG디스플레이(034220): 1
- `holding_flow_ofi_smoothing_applied` 케이피엠테크(042040): 1

## OFI/QI Micro Context

- sample_count: `19`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 19}`
- stale_missing_reason_combination_counts: `{'micro_missing': 19}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 5}`
- stale_missing_group_counts: `{'exit': 19}`
- stale_missing_group_unique_record_counts: `{'exit': 5}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 19}`
