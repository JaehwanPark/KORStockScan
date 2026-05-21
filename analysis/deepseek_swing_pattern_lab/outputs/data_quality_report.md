# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-21 ~ 2026-05-21

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `118`
- swing_ofi_qi_fact: `768`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `735`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.957`
- reason_counts: `{'micro_missing': 735, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 6, 'state_insufficient': 6}`
- reason_combination_counts: `{'micro_missing': 729, 'micro_missing+micro_not_ready+state_insufficient': 6}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 1, 'micro_missing': 1}`
- stale_missing_group_counts: `{'holding': 732, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'holding': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `115`
- sequence_fact_broker_order_forbidden_true: `115`
- ofi_qi_fact_actual_order_submitted_false: `768`
- ofi_qi_fact_broker_order_forbidden_true: `768`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 85, 'probe_observe_only': 30, 'real_order_event': 3}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 741, 'probe_observe_only': 18, 'sim_equal_weight': 9}`

## Warnings

- OFI/QI stale/missing ratio: 0.957 (735/768); reasons: micro_missing=735, micro_not_ready=6, state_insufficient=6
