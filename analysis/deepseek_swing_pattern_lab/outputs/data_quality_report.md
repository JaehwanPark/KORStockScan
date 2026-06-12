# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-12 ~ 2026-06-12

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `133`
- swing_ofi_qi_fact: `21582`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `12000`
- stale_missing_unique_record_count: `25`
- stale_missing_ratio: `0.556`
- reason_counts: `{'micro_missing': 11995, 'micro_stale': 0, 'observer_unhealthy': 22, 'micro_not_ready': 12000, 'state_insufficient': 12000}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 5, 'micro_missing+micro_not_ready+state_insufficient': 11973, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 22}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'holding': 5, 'entry': 11832, 'scale_in': 163}`
- stale_missing_group_unique_record_counts: `{'entry': 23, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 22, 'observer_unhealthy_with_other_reason': 22, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `126`
- sequence_fact_broker_order_forbidden_true: `126`
- ofi_qi_fact_actual_order_submitted_false: `21582`
- ofi_qi_fact_broker_order_forbidden_true: `21582`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 100, 'sim_equal_weight': 26, 'real_order_event': 6, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 10992, 'swing_entry_lifecycle_policy_baseline_prior_features': 10392, 'sim_equal_weight': 174, 'swing_sim_exploration_only': 24}`

## Warnings

- OFI/QI stale/missing ratio: 0.556 (12000/21582); reasons: micro_missing=11995, observer_unhealthy=22, micro_not_ready=12000, state_insufficient=12000
