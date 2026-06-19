# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-19 ~ 2026-06-19

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `67`
- swing_ofi_qi_fact: `2438`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `100`
- stale_missing_unique_record_count: `20`
- stale_missing_ratio: `0.041`
- reason_counts: `{'micro_missing': 100, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 100, 'state_insufficient': 100}`
- reason_combination_counts: `{'micro_missing+micro_not_ready+state_insufficient': 100}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 20}`
- stale_missing_group_counts: `{'entry': 100}`
- stale_missing_group_unique_record_counts: `{'entry': 20}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `66`
- sequence_fact_broker_order_forbidden_true: `66`
- ofi_qi_fact_actual_order_submitted_false: `2438`
- ofi_qi_fact_broker_order_forbidden_true: `2438`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 44, 'sim_equal_weight': 21, 'probe_observe_only': 1, 'real_order_event': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 1082, 'swing_entry_lifecycle_policy_baseline_prior_features': 910, 'sim_equal_weight': 288, 'swing_entry_lifecycle_policy': 104, 'swing_sim_exploration_only': 54}`

## Warnings

- none
