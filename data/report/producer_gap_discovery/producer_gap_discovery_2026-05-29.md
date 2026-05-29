# Producer Gap Discovery - 2026-05-29

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `producer_gap_discovery_source_only`
- candidate_count: `9`
- high_priority_candidate_count: `9`
- workorder_count: `9`
- sim_first_coverage_status: `pass`
- rolling_dates_scanned: `['2026-05-18', '2026-05-19', '2026-05-20', '2026-05-21', '2026-05-22', '2026-05-26', '2026-05-27', '2026-05-28', '2026-05-29']`
- sim_rows_scanned: `1332`
- strict_match_count: `323`
- ambiguous_match_count: `0`
- ai_two_pass_review_status: `parsed`
- ai_fail_closed: `False`
- audit_status: `pass`

## AI Review

- provider: `openai`
- model: `gpt-5.4-mini`
- warnings: `[]`

## Candidates

- `producer_gap_stop_recovery_counterfactual_missing` type=`stop_recovery_counterfactual_missing` priority=`high` samples=`93`
- `producer_gap_missed_fill_recovery_counterfactual_missing` type=`missed_fill_recovery_counterfactual_missing` priority=`high` samples=`3`
- `producer_gap_swing_sim_probe_label_gap_missing` type=`swing_sim_probe_label_gap_missing` priority=`high` samples=`7533`
- `producer_gap_scale_in_counterfactual_gap_missing` type=`scale_in_counterfactual_gap_missing` priority=`high` samples=`2808`
- `producer_gap_sim_entry_selection_gap_missing` type=`sim_entry_selection_gap_missing` priority=`high` samples=`1332`
- `producer_gap_sim_holding_runner_gap_missing` type=`sim_holding_runner_gap_missing` priority=`high` samples=`147`
- `producer_gap_sim_exit_plateau_breakdown_gap_missing` type=`sim_exit_plateau_breakdown_gap_missing` priority=`high` samples=`176`
- `producer_gap_sim_stop_recovery_gap_missing` type=`sim_stop_recovery_gap_missing` priority=`high` samples=`1380`
- `producer_gap_sim_scale_in_counterfactual_gap_missing` type=`sim_scale_in_counterfactual_gap_missing` priority=`high` samples=`25641`

## Code Improvement Orders

- `order_producer_gap_discovery_producer_gap_stop_recovery_counterfactual_missing`: Implement missing producer: stop_recovery_counterfactual_missing
- `order_producer_gap_discovery_producer_gap_missed_fill_recovery_counterfactual_missing`: Implement missing producer: missed_fill_recovery_counterfactual_missing
- `order_producer_gap_discovery_producer_gap_swing_sim_probe_label_gap_missing`: Implement missing producer: swing_sim_probe_label_gap_missing
- `order_producer_gap_discovery_producer_gap_scale_in_counterfactual_gap_missing`: Implement missing producer: scale_in_counterfactual_gap_missing
- `order_producer_gap_discovery_producer_gap_sim_entry_selection_gap_missing`: Implement missing producer: sim_entry_selection_gap_missing
- `order_producer_gap_discovery_producer_gap_sim_holding_runner_gap_missing`: Implement missing producer: sim_holding_runner_gap_missing
- `order_producer_gap_discovery_producer_gap_sim_exit_plateau_breakdown_gap_missing`: Implement missing producer: sim_exit_plateau_breakdown_gap_missing
- `order_producer_gap_discovery_producer_gap_sim_stop_recovery_gap_missing`: Implement missing producer: sim_stop_recovery_gap_missing
- `order_producer_gap_discovery_producer_gap_sim_scale_in_counterfactual_gap_missing`: Implement missing producer: sim_scale_in_counterfactual_gap_missing
