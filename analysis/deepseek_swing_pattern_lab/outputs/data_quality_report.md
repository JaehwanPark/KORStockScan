# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-22 ~ 2026-05-22

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `101`
- swing_ofi_qi_fact: `565`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `517`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `0.915`
- reason_counts: `{'micro_missing': 517, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 1, 'state_insufficient': 1}`
- reason_combination_counts: `{'micro_missing': 516, 'micro_missing+micro_not_ready+state_insufficient': 1}`
- reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'holding': 517}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `98`
- sequence_fact_broker_order_forbidden_true: `98`
- ofi_qi_fact_actual_order_submitted_false: `565`
- ofi_qi_fact_broker_order_forbidden_true: `565`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 75, 'probe_observe_only': 24, 'real_order_event': 2}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 527, 'probe_observe_only': 28, 'sim_equal_weight': 10}`

## Warnings

- OFI/QI stale/missing ratio: 0.915 (517/565); reasons: micro_missing=517, micro_not_ready=1, state_insufficient=1
