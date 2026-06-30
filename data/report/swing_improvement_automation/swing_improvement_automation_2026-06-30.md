# Swing Improvement Automation - 2026-06-30

- Runtime change: `false`
- Generated orders are inputs for `build_code_improvement_workorder`; implementation is manual.
- simulation_opportunity_sample_state: `hold_sample`
- simulation_opportunity_closed/winner: `0` / `0`

## Orders

| order_id | stage | subsystem | route | family | priority |
| --- | --- | --- | --- | --- | ---: |
| `order_swing_ofi_qi_stale_or_missing_context` | `entry` | `swing_orderbook_micro_context` | `existing_family` | `swing_entry_ofi_qi_execution_quality` | 4 |
| `order_swing_holding_exit_contract_gap_review` | `holding_exit` | `swing_holding_exit` | `instrumentation_order` | `swing_exit_ofi_qi_smoothing` | 4 |
| `order_swing_scale_in_contract_gap_review` | `scale_in` | `swing_scale_in` | `instrumentation_order` | `swing_scale_in_ofi_qi_confirmation` | 4 |
| `order_swing_discovery_label_contract_gap_review` | `selection` | `swing_strategy_discovery` | `instrumentation_order` | `-` | 5 |
| `order_swing_exit_ofi_qi_smoothing_distribution` | `holding_exit` | `swing_holding_exit` | `existing_family` | `swing_exit_ofi_qi_smoothing` | 6 |
| `order_swing_ai_contract_structured_output_eval` | `ai_contract` | `swing_ai_contract` | `auto_family_candidate` | `-` | 5 |
| `order_swing_scale_in_avg_down_pyramid_observation` | `scale_in` | `swing_scale_in` | `auto_family_candidate` | `-` | 6 |
