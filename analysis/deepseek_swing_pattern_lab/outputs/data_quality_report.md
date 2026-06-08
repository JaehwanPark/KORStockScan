# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-08 ~ 2026-06-08

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `131`
- swing_ofi_qi_fact: `27130`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `16284`
- stale_missing_unique_record_count: `23`
- stale_missing_ratio: `0.6002`
- reason_counts: `{'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}`
- stale_missing_group_counts: `{'holding': 9, 'scale_in': 39, 'entry': 16232, 'other': 4}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2, 'entry': 22, 'other': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `109`
- sequence_fact_broker_order_forbidden_true: `109`
- ofi_qi_fact_actual_order_submitted_false: `27130`
- ofi_qi_fact_broker_order_forbidden_true: `27130`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 92, 'real_order_event': 22, 'sim_equal_weight': 16, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 13773, 'swing_entry_lifecycle_policy': 13053, 'swing_entry_lifecycle_policy_baseline_prior_features': 178, 'sim_equal_weight': 95, 'swing_sim_exploration_only': 31}`

## Warnings

- OFI/QI stale/missing ratio: 0.6002 (16284/27130); reasons: micro_missing=16275, observer_unhealthy=3563, micro_not_ready=16249, state_insufficient=16249
