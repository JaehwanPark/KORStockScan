# Swing Selection Funnel Report - 2026-06-29

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
| `holding_flow_ofi_smoothing_applied` | 15 | 8 |

## Top Code Stage

- `holding_flow_ofi_smoothing_applied` 성신양회(004980): 4
- `holding_flow_ofi_smoothing_applied` 테스(095610): 2
- `holding_flow_ofi_smoothing_applied` 브이엠(089970): 2
- `holding_flow_ofi_smoothing_applied` 금호타이어(073240): 2
- `holding_flow_ofi_smoothing_applied` 올릭스(226950): 2
- `holding_flow_ofi_smoothing_applied` 한올바이오파마(009420): 1
- `holding_flow_ofi_smoothing_applied` 아세아시멘트(183190): 1
- `holding_flow_ofi_smoothing_applied` 에코프로비엠(247540): 1

## OFI/QI Micro Context

- sample_count: `15`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `1.0`
- stale_missing_reason_counts: `{'micro_missing': 15}`
- stale_missing_reason_combination_counts: `{'micro_missing': 15}`
- stale_missing_reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'exit': 15}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- entry_micro_state_counts: `{}`
- scale_in_micro_state_counts: `{}`
- exit_smoothing_action_counts: `{'NO_CHANGE': 15}`
