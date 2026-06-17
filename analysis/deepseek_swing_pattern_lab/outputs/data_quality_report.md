# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-17 ~ 2026-06-17

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `129`
- swing_ofi_qi_fact: `90023`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `12312`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.1368`
- reason_counts: `{'micro_missing': 12301, 'micro_stale': 0, 'observer_unhealthy': 4, 'micro_not_ready': 12312, 'state_insufficient': 12312}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 11, 'micro_missing+micro_not_ready+state_insufficient': 12297, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 11, 'entry': 12294, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 4, 'observer_unhealthy_with_other_reason': 4, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `129`
- sequence_fact_broker_order_forbidden_true: `129`
- ofi_qi_fact_actual_order_submitted_false: `90023`
- ofi_qi_fact_broker_order_forbidden_true: `90023`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 112, 'sim_equal_weight': 16, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 89941, 'sim_equal_weight': 73, 'swing_sim_exploration_only': 9}`

## Warnings

- none
