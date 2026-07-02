# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-07-02 ~ 2026-07-02

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `32`
- swing_ofi_qi_fact: `25`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `5`
- stale_missing_unique_record_count: `1`
- stale_missing_ratio: `0.2`
- reason_counts: `{'micro_missing': 0, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 5, 'state_insufficient': 5}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 5}`
- reason_combination_unique_record_counts: `{'micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 5}`
- stale_missing_group_unique_record_counts: `{'holding': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `13`
- sequence_fact_broker_order_forbidden_true: `13`
- ofi_qi_fact_actual_order_submitted_false: `25`
- ofi_qi_fact_broker_order_forbidden_true: `25`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'real_order_event': 19, 'source_quality_only': 13}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 25}`

## Warnings

- none
