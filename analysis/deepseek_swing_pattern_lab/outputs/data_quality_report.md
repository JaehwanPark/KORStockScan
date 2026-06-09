# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-09 ~ 2026-06-09

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `121`
- swing_ofi_qi_fact: `26948`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `11983`
- stale_missing_unique_record_count: `4`
- stale_missing_ratio: `0.4447`
- reason_counts: `{'micro_missing': 11973, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 11983, 'state_insufficient': 11983}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 11973}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'holding': 10, 'entry': 11959, 'scale_in': 12, 'exit': 2}`
- stale_missing_group_unique_record_counts: `{'entry': 4, 'scale_in': 1, 'exit': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `119`
- sequence_fact_broker_order_forbidden_true: `119`
- ofi_qi_fact_actual_order_submitted_false: `26948`
- ofi_qi_fact_broker_order_forbidden_true: `26948`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 110, 'sim_equal_weight': 8, 'real_order_event': 2, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 13776, 'swing_entry_lifecycle_policy_baseline_prior_features': 13097, 'sim_equal_weight': 41, 'swing_sim_exploration_only': 34}`

## Warnings

- OFI/QI stale/missing ratio: 0.4447 (11983/26948); reasons: micro_missing=11973, micro_not_ready=11983, state_insufficient=11983
