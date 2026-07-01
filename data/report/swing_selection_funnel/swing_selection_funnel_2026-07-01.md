# Swing Selection Funnel Report - 2026-07-01

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
| `holding_flow_ofi_smoothing_applied` | 57 | 12 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 제룡전기(033100): 23
- `holding_flow_ofi_smoothing_applied` 가온전선(000500): 10
- `holding_flow_ofi_smoothing_applied` 광주신세계(037710): 7
- `holding_flow_ofi_smoothing_applied` 엑스게이트(356680): 5
- `holding_flow_ofi_smoothing_applied` 금호타이어(073240): 3
- `holding_flow_ofi_smoothing_applied` 대화제약(067080): 2
- `holding_flow_ofi_smoothing_applied` 삼표시멘트(038500): 2
- `holding_flow_ofi_smoothing_applied` 한양이엔지(045100): 2
- `holding_flow_ofi_smoothing_applied` LS ELECTRIC(010120): 1
- `holding_flow_ofi_smoothing_applied` 에코프로비엠(247540): 1

## OFI/QI Micro Context

- sample_count: `57`
- stale_missing_unique_record_count: `11`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 57, 'micro_not_ready': 49, 'state_insufficient': 49, 'observer_unhealthy': 32}`
- stale_missing_reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 19, 'micro_missing': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 30, 'micro_missing+observer_unhealthy': 2}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 7, 'micro_missing': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4, 'micro_missing+observer_unhealthy': 1}`
- stale_missing_group_counts: `{'exit': 57}`
- stale_missing_group_unique_record_counts: `{'exit': 11}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 32, 'observer_unhealthy_with_other_reason': 32, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 57}`
