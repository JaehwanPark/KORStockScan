# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-26 ~ 2026-05-26

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `125`
- swing_ofi_qi_fact: `872`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `4`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `0.0046`
- reason_counts: `{'micro_missing': 1, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 4, 'state_insufficient': 4}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 3, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 3, 'exit': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `115`
- sequence_fact_broker_order_forbidden_true: `115`
- ofi_qi_fact_actual_order_submitted_false: `872`
- ofi_qi_fact_broker_order_forbidden_true: `872`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 92, 'probe_observe_only': 24, 'real_order_event': 9}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 813, 'probe_observe_only': 40, 'sim_equal_weight': 19}`

## Warnings

- none
