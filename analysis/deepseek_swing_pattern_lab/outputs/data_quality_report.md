# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-07-09 ~ 2026-07-09

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `11`
- swing_ofi_qi_fact: `6`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `0`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `0.0`
- reason_counts: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 0, 'state_insufficient': 0}`
- reason_combination_counts: `{}`
- reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `5`
- sequence_fact_broker_order_forbidden_true: `5`
- ofi_qi_fact_actual_order_submitted_false: `6`
- ofi_qi_fact_broker_order_forbidden_true: `6`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'real_order_event': 6, 'source_quality_only': 5}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 6}`

## Warnings

- none
