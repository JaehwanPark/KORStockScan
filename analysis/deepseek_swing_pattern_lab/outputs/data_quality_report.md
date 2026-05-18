# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-18 ~ 2026-05-18

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `55`
- swing_ofi_qi_fact: `158`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `68`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.4304`
- reason_counts: `{'micro_missing': 68, 'micro_stale': 0, 'observer_unhealthy': 6, 'micro_not_ready': 6, 'state_insufficient': 6}`
- reason_combination_counts: `{'micro_missing': 62, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'holding': 62, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `55`
- sequence_fact_broker_order_forbidden_true: `55`
- ofi_qi_fact_actual_order_submitted_false: `158`
- ofi_qi_fact_broker_order_forbidden_true: `158`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'probe_observe_only': 53, 'source_quality_only': 2}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 82, 'probe_observe_only': 57, 'sim_equal_weight': 19}`

## Warnings

- OFI/QI stale/missing ratio: 0.4304 (68/158); reasons: micro_missing=68, observer_unhealthy=6, micro_not_ready=6, state_insufficient=6
