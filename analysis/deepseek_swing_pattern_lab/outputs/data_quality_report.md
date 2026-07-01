# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-07-01 ~ 2026-07-01

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `36`
- swing_ofi_qi_fact: `57`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `51`
- stale_missing_unique_record_count: `8`
- stale_missing_ratio: `0.8947`
- reason_counts: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 32, 'micro_not_ready': 49, 'state_insufficient': 49}`
- reason_combination_counts: `{'observer_unhealthy+micro_not_ready+state_insufficient': 30, 'observer_unhealthy': 2, 'micro_not_ready+state_insufficient': 19}`
- reason_combination_unique_record_counts: `{'observer_unhealthy+micro_not_ready+state_insufficient': 4, 'observer_unhealthy': 1, 'micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'holding': 51}`
- stale_missing_group_unique_record_counts: `{'holding': 8}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 32, 'observer_unhealthy_with_other_reason': 30, 'observer_unhealthy_only': 2}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `9`
- sequence_fact_broker_order_forbidden_true: `9`
- ofi_qi_fact_actual_order_submitted_false: `57`
- ofi_qi_fact_broker_order_forbidden_true: `57`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'real_order_event': 27, 'source_quality_only': 9}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 57}`

## Warnings

- OFI/QI stale/missing ratio: 0.8947 (51/57); reasons: observer_unhealthy=32, micro_not_ready=49, state_insufficient=49
