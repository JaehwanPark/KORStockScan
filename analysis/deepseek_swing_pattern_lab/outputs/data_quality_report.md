# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-01 ~ 2026-06-01

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `120`
- swing_ofi_qi_fact: `46863`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `226`
- stale_missing_unique_record_count: `5`
- stale_missing_ratio: `0.0048`
- reason_counts: `{'micro_missing': 215, 'micro_stale': 0, 'observer_unhealthy': 0, 'micro_not_ready': 226, 'state_insufficient': 226}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 11, 'micro_missing+micro_not_ready+state_insufficient': 215}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 5}`
- stale_missing_group_counts: `{'holding': 11, 'entry': 215}`
- stale_missing_group_unique_record_counts: `{'entry': 5}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `108`
- sequence_fact_broker_order_forbidden_true: `108`
- ofi_qi_fact_actual_order_submitted_false: `46863`
- ofi_qi_fact_broker_order_forbidden_true: `46863`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 100, 'real_order_event': 12, 'probe_observe_only': 8}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 23973, 'swing_entry_lifecycle_policy_baseline_prior_features': 22832, 'probe_observe_only': 33, 'sim_equal_weight': 25}`

## Warnings

- none
