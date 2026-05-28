# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-28 ~ 2026-05-28

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `106`
- swing_ofi_qi_fact: `29061`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `3154`
- stale_missing_unique_record_count: `15`
- stale_missing_ratio: `0.1085`
- reason_counts: `{'micro_missing': 3150, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 3154, 'state_insufficient': 3154}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 4, 'micro_missing+micro_not_ready+state_insufficient': 3142, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 13, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'holding': 4, 'scale_in': 3, 'entry': 3146, 'other': 1}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'entry': 14, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `106`
- sequence_fact_broker_order_forbidden_true: `106`
- ofi_qi_fact_actual_order_submitted_false: `29061`
- ofi_qi_fact_broker_order_forbidden_true: `29061`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 82, 'probe_observe_only': 23, 'sim_equal_weight': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 14746, 'swing_entry_lifecycle_policy': 10383, 'swing_entry_lifecycle_policy_baseline_prior_features': 3877, 'sim_equal_weight': 37, 'probe_observe_only': 18}`

## Warnings

- none
