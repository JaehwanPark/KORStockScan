# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-19 ~ 2026-05-19

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `80`
- swing_ofi_qi_fact: `510`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `470`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.9216`
- reason_counts: `{'micro_missing': 470, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 24, 'state_insufficient': 24}`
- reason_combination_counts: `{'micro_missing': 446, 'micro_missing+micro_not_ready+state_insufficient': 23, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'holding': 463, 'exit': 4, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'exit': 4, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `80`
- sequence_fact_broker_order_forbidden_true: `80`
- ofi_qi_fact_actual_order_submitted_false: `510`
- ofi_qi_fact_broker_order_forbidden_true: `510`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 50, 'probe_observe_only': 30}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 474, 'probe_observe_only': 25, 'sim_equal_weight': 11}`

## Warnings

- OFI/QI stale/missing ratio: 0.9216 (470/510); reasons: micro_missing=470, observer_unhealthy=1, micro_not_ready=24, state_insufficient=24
