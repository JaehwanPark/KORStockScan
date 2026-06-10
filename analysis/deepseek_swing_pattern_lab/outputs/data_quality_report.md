# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-10 ~ 2026-06-10

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `141`
- swing_ofi_qi_fact: `37158`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `2626`
- stale_missing_unique_record_count: `27`
- stale_missing_ratio: `0.0707`
- reason_counts: `{'micro_missing': 2611, 'micro_stale': 0, 'observer_unhealthy': 16, 'micro_not_ready': 2626, 'state_insufficient': 2626}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 15, 'micro_missing+micro_not_ready+state_insufficient': 2595, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 25, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 9}`
- stale_missing_group_counts: `{'holding': 15, 'exit': 1, 'entry': 2607, 'scale_in': 2, 'other': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 1, 'entry': 26, 'scale_in': 1, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 16, 'observer_unhealthy_with_other_reason': 16, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `130`
- sequence_fact_broker_order_forbidden_true: `130`
- ofi_qi_fact_actual_order_submitted_false: `37158`
- ofi_qi_fact_broker_order_forbidden_true: `37158`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 105, 'sim_equal_weight': 24, 'real_order_event': 11, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 18841, 'swing_entry_lifecycle_policy': 16182, 'swing_entry_lifecycle_policy_baseline_prior_features': 1909, 'sim_equal_weight': 183, 'swing_sim_exploration_only': 43}`

## Warnings

- none
