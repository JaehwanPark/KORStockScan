# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-02 ~ 2026-06-02

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `139`
- swing_ofi_qi_fact: `52692`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `5496`
- stale_missing_unique_record_count: `16`
- stale_missing_ratio: `0.1043`
- reason_counts: `{'micro_missing': 5487, 'micro_stale': 0, 'observer_unhealthy': 1, 'micro_not_ready': 5496, 'state_insufficient': 5496}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 9, 'micro_missing+micro_not_ready+state_insufficient': 5486, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 16, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 9, 'entry': 5486, 'other': 1}`
- stale_missing_group_unique_record_counts: `{'entry': 16, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 1, 'observer_unhealthy_with_other_reason': 1, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `120`
- sequence_fact_broker_order_forbidden_true: `120`
- ofi_qi_fact_actual_order_submitted_false: `52692`
- ofi_qi_fact_broker_order_forbidden_true: `52692`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 98, 'probe_observe_only': 22, 'real_order_event': 18, 'sim_equal_weight': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 26693, 'swing_entry_lifecycle_policy': 17588, 'swing_entry_lifecycle_policy_baseline_prior_features': 8359, 'sim_equal_weight': 27, 'probe_observe_only': 25}`

## Warnings

- none
