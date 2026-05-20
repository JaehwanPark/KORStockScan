# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-20 ~ 2026-05-20

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `104`
- swing_ofi_qi_fact: `666`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `636`
- stale_missing_unique_record_count: `2`
- stale_missing_ratio: `0.955`
- reason_counts: `{'micro_missing': 636, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 20, 'state_insufficient': 20}`
- reason_combination_counts: `{'micro_missing': 615, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 20}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'holding': 630, 'scale_in': 6}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `100`
- sequence_fact_broker_order_forbidden_true: `100`
- ofi_qi_fact_actual_order_submitted_false: `666`
- ofi_qi_fact_broker_order_forbidden_true: `666`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 68, 'probe_observe_only': 32, 'real_order_event': 4}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 639, 'probe_observe_only': 18, 'sim_equal_weight': 9}`

## Warnings

- OFI/QI stale/missing ratio: 0.955 (636/666); reasons: micro_missing=636, observer_unhealthy=1, micro_not_ready=20, state_insufficient=20
