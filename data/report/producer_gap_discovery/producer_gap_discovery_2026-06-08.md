# Producer Gap Discovery - 2026-06-08

## Summary

- status: `pass`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `producer_gap_discovery_source_only`
- candidate_count: `10`
- high_priority_candidate_count: `10`
- workorder_count: `0`
- sim_first_coverage_status: `pass`
- rolling_dates_scanned: `['2026-05-18', '2026-05-19', '2026-05-20', '2026-05-21', '2026-05-22', '2026-05-26', '2026-05-27', '2026-05-28', '2026-05-29', '2026-06-01', '2026-06-02', '2026-06-04', '2026-06-05', '2026-06-08']`
- sim_rows_scanned: `2717`
- strict_match_count: `1040`
- ambiguous_match_count: `0`
- ai_two_pass_review_status: `parsed`
- ai_fail_closed: `False`
- audit_status: `pass`

## AI Review

- provider: `openai`
- model: `gpt-5.4-mini`
- warnings: `[]`

## Candidates

- `producer_gap_stop_recovery_counterfactual_missing` type=`stop_recovery_counterfactual_missing` priority=`high` samples=`274`
- `producer_gap_missed_fill_recovery_counterfactual_missing` type=`missed_fill_recovery_counterfactual_missing` priority=`high` samples=`6`
- `producer_gap_swing_sim_probe_label_gap_missing` type=`swing_sim_probe_label_gap_missing` priority=`high` samples=`7070`
- `producer_gap_scale_in_counterfactual_gap_missing` type=`scale_in_counterfactual_gap_missing` priority=`high` samples=`2535`
- `producer_gap_limit_up_plateau_breakdown_exit_missing` type=`limit_up_plateau_breakdown_exit_missing` priority=`high` samples=`1`
- `producer_gap_sim_entry_selection_gap_missing` type=`sim_entry_selection_gap_missing` priority=`high` samples=`2717`
- `producer_gap_sim_holding_runner_gap_missing` type=`sim_holding_runner_gap_missing` priority=`high` samples=`453`
- `producer_gap_sim_exit_plateau_breakdown_gap_missing` type=`sim_exit_plateau_breakdown_gap_missing` priority=`high` samples=`587`
- `producer_gap_sim_stop_recovery_gap_missing` type=`sim_stop_recovery_gap_missing` priority=`high` samples=`3416`
- `producer_gap_sim_scale_in_counterfactual_gap_missing` type=`sim_scale_in_counterfactual_gap_missing` priority=`high` samples=`27814`

## Code Improvement Orders

