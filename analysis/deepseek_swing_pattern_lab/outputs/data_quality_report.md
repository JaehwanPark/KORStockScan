# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-28 ~ 2026-05-28

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `112`
- swing_ofi_qi_fact: `39982`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `4078`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `0.102`
- reason_counts: `{'micro_missing': 4070, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 4078, 'state_insufficient': 4078}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 8, 'micro_missing+micro_not_ready+state_insufficient': 4062, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3}`
- stale_missing_group_counts: `{'holding': 8, 'scale_in': 3, 'entry': 4065, 'other': 2}`
- stale_missing_group_unique_record_counts: `{'scale_in': 1, 'entry': 17, 'other': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `112`
- sequence_fact_broker_order_forbidden_true: `112`
- ofi_qi_fact_actual_order_submitted_false: `39982`
- ofi_qi_fact_broker_order_forbidden_true: `39982`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 88, 'probe_observe_only': 23, 'sim_equal_weight': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 20212, 'swing_entry_lifecycle_policy': 14954, 'swing_entry_lifecycle_policy_baseline_prior_features': 4721, 'sim_equal_weight': 72, 'probe_observe_only': 23}`

## Warnings

- none
