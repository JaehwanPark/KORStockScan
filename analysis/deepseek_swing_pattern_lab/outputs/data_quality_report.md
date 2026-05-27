# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-27 ~ 2026-05-27

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `114`
- swing_ofi_qi_fact: `70459`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `3835`
- stale_missing_unique_record_count: `20`
- stale_missing_ratio: `0.0544`
- reason_counts: `{'micro_missing': 3832, 'micro_stale': 0, 'observer_unhealthy': 39, 'micro_not_ready': 3835, 'state_insufficient': 3835}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 3, 'micro_missing+micro_not_ready+state_insufficient': 3793, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 39}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 20, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 11}`
- stale_missing_group_counts: `{'holding': 3, 'exit': 2, 'entry': 3821, 'scale_in': 5, 'other': 4}`
- stale_missing_group_unique_record_counts: `{'exit': 1, 'entry': 19, 'scale_in': 2, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 39, 'observer_unhealthy_with_other_reason': 39, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `106`
- sequence_fact_broker_order_forbidden_true: `106`
- ofi_qi_fact_actual_order_submitted_false: `70459`
- ofi_qi_fact_broker_order_forbidden_true: `70459`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 86, 'probe_observe_only': 21, 'real_order_event': 7}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 35321, 'swing_entry_lifecycle_policy_baseline_prior_features': 25224, 'swing_entry_lifecycle_policy': 9661, 'sim_equal_weight': 218, 'probe_observe_only': 35}`

## Warnings

- none
