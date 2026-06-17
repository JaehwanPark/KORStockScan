# Producer Gap Discovery - 2026-06-17

## Summary

- status: `pass`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `producer_gap_discovery_source_only`
- candidate_count: `9`
- high_priority_candidate_count: `9`
- workorder_count: `0`
- sim_first_coverage_status: `pass`
- rolling_dates_scanned: `['2026-06-17']`
- sim_rows_scanned: `169`
- strict_match_count: `19`
- ambiguous_match_count: `0`
- ai_two_pass_review_status: `parsed`
- ai_fail_closed: `False`
- audit_status: `pass`

## AI Review

- provider: `openai`
- model: `qwen.qwen3-235b-a22b-2507-v1:0`
- warnings: `[]`

## Candidates

- `producer_gap_stop_recovery_counterfactual_missing` type=`stop_recovery_counterfactual_missing` priority=`high` samples=`129`
- `producer_gap_missed_fill_recovery_counterfactual_missing` type=`missed_fill_recovery_counterfactual_missing` priority=`high` samples=`6`
- `producer_gap_swing_sim_probe_label_gap_missing` type=`swing_sim_probe_label_gap_missing` priority=`high` samples=`8248`
- `producer_gap_scale_in_counterfactual_gap_missing` type=`scale_in_counterfactual_gap_missing` priority=`high` samples=`3941`
- `producer_gap_sim_entry_selection_gap_missing` type=`sim_entry_selection_gap_missing` priority=`high` samples=`169`
- `producer_gap_sim_holding_runner_gap_missing` type=`sim_holding_runner_gap_missing` priority=`high` samples=`6`
- `producer_gap_sim_exit_plateau_breakdown_gap_missing` type=`sim_exit_plateau_breakdown_gap_missing` priority=`high` samples=`13`
- `producer_gap_sim_stop_recovery_gap_missing` type=`sim_stop_recovery_gap_missing` priority=`high` samples=`258`
- `producer_gap_sim_scale_in_counterfactual_gap_missing` type=`sim_scale_in_counterfactual_gap_missing` priority=`high` samples=`33631`

## Code Improvement Orders

