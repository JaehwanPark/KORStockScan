# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-30 ~ 2026-06-30

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `51`
- swing_ofi_qi_fact: `165`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `22`
- stale_missing_unique_record_count: `3`
- stale_missing_ratio: `0.1333`
- reason_counts: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 4, 'micro_not_ready': 22, 'state_insufficient': 22}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 18, 'observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- reason_combination_unique_record_counts: `{'micro_not_ready+state_insufficient': 3, 'observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 22}`
- stale_missing_group_unique_record_counts: `{'holding': 3}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `17`
- sequence_fact_broker_order_forbidden_true: `17`
- ofi_qi_fact_actual_order_submitted_false: `165`
- ofi_qi_fact_broker_order_forbidden_true: `165`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'real_order_event': 34, 'source_quality_only': 17}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 165}`

## Warnings

- none
