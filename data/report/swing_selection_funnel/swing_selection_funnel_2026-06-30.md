# Swing Selection Funnel Report - 2026-06-30

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
| `holding_flow_ofi_smoothing_applied` | 165 | 29 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 에코프로비엠(247540): 47
- `holding_flow_ofi_smoothing_applied` 후성(093370): 38
- `holding_flow_ofi_smoothing_applied` LG전자(066570): 17
- `holding_flow_ofi_smoothing_applied` 제룡전기(033100): 9
- `holding_flow_ofi_smoothing_applied` 가온전선(000500): 7
- `holding_flow_ofi_smoothing_applied` 삼성전자(005930): 7
- `holding_flow_ofi_smoothing_applied` 금호건설(002990): 6
- `holding_flow_ofi_smoothing_applied` 심텍(222800): 6
- `holding_flow_ofi_smoothing_applied` 원익IPS(240810): 5
- `holding_flow_ofi_smoothing_applied` 비나텍(126340): 4

## OFI/QI Micro Context

- sample_count: `165`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 165, 'micro_not_ready': 22, 'state_insufficient': 22, 'observer_unhealthy': 4}`
- stale_missing_reason_combination_counts: `{'micro_missing': 143, 'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_reason_combination_unique_record_counts: `{'micro_missing': 18, 'micro_missing+micro_not_ready+state_insufficient': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'exit': 165}`
- stale_missing_group_unique_record_counts: `{'exit': 18}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 164, 'CONFIRM_EXIT': 1}`
