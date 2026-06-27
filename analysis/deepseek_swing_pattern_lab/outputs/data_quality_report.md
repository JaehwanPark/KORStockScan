# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-26 ~ 2026-06-26

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `20`
- swing_ofi_qi_fact: `37`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `4`
- stale_missing_unique_record_count: `0`
- stale_missing_ratio: `0.1081`
- reason_counts: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 4, 'state_insufficient': 4}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 4}`
- reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{'holding': 4}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `13`
- sequence_fact_broker_order_forbidden_true: `13`
- ofi_qi_fact_actual_order_submitted_false: `37`
- ofi_qi_fact_broker_order_forbidden_true: `37`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 13, 'real_order_event': 7}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 37}`

## Warnings

- none
