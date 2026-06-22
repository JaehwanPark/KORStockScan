# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-22 ~ 2026-06-22

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `67`
- swing_ofi_qi_fact: `1873`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `42`
- stale_missing_unique_record_count: `7`
- stale_missing_ratio: `0.0224`
- reason_counts: `{'micro_missing': 41, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 42, 'state_insufficient': 42}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 41}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'holding': 1, 'entry': 40, 'exit': 1}`
- stale_missing_group_unique_record_counts: `{'entry': 7, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `67`
- sequence_fact_broker_order_forbidden_true: `67`
- ofi_qi_fact_actual_order_submitted_false: `1873`
- ofi_qi_fact_broker_order_forbidden_true: `1873`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 59, 'sim_equal_weight': 7, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 890, 'swing_entry_lifecycle_policy_baseline_prior_features': 813, 'sim_equal_weight': 140, 'swing_sim_exploration_only': 30}`

## Warnings

- none
