# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-04 ~ 2026-06-04

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `33`
- swing_ofi_qi_fact: `9094`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `294`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.0323`
- reason_counts: `{'micro_missing': 293, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 294, 'state_insufficient': 294}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 285, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'holding': 1, 'entry': 292, 'other': 1}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `32`
- sequence_fact_broker_order_forbidden_true: `32`
- ofi_qi_fact_actual_order_submitted_false: `9094`
- ofi_qi_fact_broker_order_forbidden_true: `9094`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 20, 'sim_equal_weight': 11, 'probe_observe_only': 1, 'real_order_event': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 4542, 'swing_entry_lifecycle_policy_baseline_prior_features': 4507, 'sim_equal_weight': 43, 'swing_sim_exploration_only': 2}`

## Warnings

- none
