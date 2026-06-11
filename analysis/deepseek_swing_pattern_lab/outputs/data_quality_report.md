# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-11 ~ 2026-06-11

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `145`
- swing_ofi_qi_fact: `18261`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `845`
- stale_missing_unique_record_count: `15`
- stale_missing_ratio: `0.0463`
- reason_counts: `{'micro_missing': 842, 'micro_stale': 0, 'observer_unhealthy': 3, 'micro_not_ready': 845, 'state_insufficient': 845}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 3, 'micro_missing+micro_not_ready+state_insufficient': 839, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 14, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 3, 'entry': 838, 'other': 1, 'scale_in': 3}`
- stale_missing_group_unique_record_counts: `{'entry': 14, 'other': 1, 'scale_in': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3, 'observer_unhealthy_with_other_reason': 3, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `143`
- sequence_fact_broker_order_forbidden_true: `143`
- ofi_qi_fact_actual_order_submitted_false: `18261`
- ofi_qi_fact_broker_order_forbidden_true: `18261`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 111, 'sim_equal_weight': 31, 'real_order_event': 2, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 9267, 'swing_entry_lifecycle_policy_baseline_prior_features': 7582, 'swing_entry_lifecycle_policy': 1225, 'sim_equal_weight': 136, 'swing_sim_exploration_only': 51}`

## Warnings

- none
