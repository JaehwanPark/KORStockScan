# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-05 ~ 2026-06-05

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `80`
- swing_ofi_qi_fact: `47943`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `2999`
- stale_missing_unique_record_count: `15`
- stale_missing_ratio: `0.0626`
- reason_counts: `{'micro_missing': 2992, 'micro_stale': 0, 'observer_unhealthy': 6, 'micro_not_ready': 2999, 'state_insufficient': 2999}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 7, 'micro_missing+micro_not_ready+state_insufficient': 2986, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'holding': 7, 'entry': 2992}`
- stale_missing_group_unique_record_counts: `{'entry': 15}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 6, 'observer_unhealthy_with_other_reason': 6, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `79`
- sequence_fact_broker_order_forbidden_true: `79`
- ofi_qi_fact_actual_order_submitted_false: `47943`
- ofi_qi_fact_broker_order_forbidden_true: `47943`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 66, 'sim_equal_weight': 12, 'probe_observe_only': 1, 'real_order_event': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 24154, 'swing_entry_lifecycle_policy': 23589, 'swing_entry_lifecycle_policy_baseline_prior_features': 106, 'sim_equal_weight': 50, 'swing_sim_exploration_only': 44}`

## Warnings

- none
