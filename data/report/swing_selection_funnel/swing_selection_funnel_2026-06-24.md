# Swing Selection Funnel Report - 2026-06-24

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
| `holding_flow_ofi_smoothing_applied` | 30 | 21 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 미래나노텍(095500): 5
- `holding_flow_ofi_smoothing_applied` 엑스게이트(356680): 4
- `holding_flow_ofi_smoothing_applied` SK스퀘어(402340): 2
- `holding_flow_ofi_smoothing_applied` 한올바이오파마(009420): 2
- `holding_flow_ofi_smoothing_applied` 두산로보틱스(454910): 2
- `holding_flow_ofi_smoothing_applied` 한화오션(042660): 1
- `holding_flow_ofi_smoothing_applied` 대원전선(006340): 1
- `holding_flow_ofi_smoothing_applied` 계양전기(012200): 1
- `holding_flow_ofi_smoothing_applied` LG이노텍(011070): 1
- `holding_flow_ofi_smoothing_applied` 삼화콘덴서(001820): 1

## OFI/QI Micro Context

- sample_count: `30`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 30}`
- stale_missing_reason_combination_counts: `{'micro_missing': 30}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 1}`
- stale_missing_group_counts: `{'exit': 30}`
- stale_missing_group_unique_record_counts: `{'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 29, 'CONFIRM_EXIT': 1}`
