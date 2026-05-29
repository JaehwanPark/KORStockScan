# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-05-29 ~ 2026-05-29

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `101`
- swing_ofi_qi_fact: `30264`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `2890`
- stale_missing_unique_record_count: `17`
- stale_missing_ratio: `0.0955`
- reason_counts: `{'micro_missing': 2880, 'micro_stale': 0, 'observer_unhealthy': 8, 'micro_not_ready': 2890, 'state_insufficient': 2890}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 10, 'micro_missing+micro_not_ready+state_insufficient': 2872, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 8}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 17, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 2}`
- stale_missing_group_counts: `{'holding': 10, 'entry': 2877, 'other': 3}`
- stale_missing_group_unique_record_counts: `{'entry': 17, 'other': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 8, 'observer_unhealthy_with_other_reason': 8, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `97`
- sequence_fact_broker_order_forbidden_true: `97`
- ofi_qi_fact_actual_order_submitted_false: `30264`
- ofi_qi_fact_broker_order_forbidden_true: `30264`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 80, 'probe_observe_only': 16, 'real_order_event': 4, 'sim_equal_weight': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 15296, 'swing_entry_lifecycle_policy_baseline_prior_features': 14822, 'sim_equal_weight': 121, 'probe_observe_only': 25}`

## Warnings

- none
