# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-23 ~ 2026-06-23

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `49`
- swing_ofi_qi_fact: `4427`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `3676`
- stale_missing_unique_record_count: `8`
- stale_missing_ratio: `0.8304`
- reason_counts: `{'micro_missing': 3675, 'micro_stale': 0, 'observer_unhealthy': 216, 'micro_not_ready': 3676, 'state_insufficient': 3676}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 3459, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 216}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 8, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 4}`
- stale_missing_group_counts: `{'holding': 1, 'exit': 5, 'entry': 3645, 'scale_in': 6, 'other': 19}`
- stale_missing_group_unique_record_counts: `{'exit': 5, 'entry': 6, 'scale_in': 2, 'other': 4}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 216, 'observer_unhealthy_with_other_reason': 216, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `48`
- sequence_fact_broker_order_forbidden_true: `48`
- ofi_qi_fact_actual_order_submitted_false: `4427`
- ofi_qi_fact_broker_order_forbidden_true: `4427`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 39, 'sim_equal_weight': 8, 'probe_observe_only': 1, 'real_order_event': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 2191, 'swing_entry_lifecycle_policy': 1921, 'swing_entry_lifecycle_policy_baseline_prior_features': 162, 'sim_equal_weight': 98, 'swing_sim_exploration_only': 55}`

## Warnings

- OFI/QI stale/missing ratio: 0.8304 (3676/4427); reasons: micro_missing=3675, observer_unhealthy=216, micro_not_ready=3676, state_insufficient=3676
