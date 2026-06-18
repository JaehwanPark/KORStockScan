# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-18 ~ 2026-06-18

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `127`
- swing_ofi_qi_fact: `8917`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `1345`
- stale_missing_unique_record_count: `25`
- stale_missing_ratio: `0.1508`
- reason_counts: `{'micro_missing': 1337, 'micro_stale': 0, 'observer_unhealthy': 444, 'micro_not_ready': 1101, 'state_insufficient': 1101}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 6, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 200, 'micro_missing+micro_not_ready+state_insufficient': 895, 'micro_missing+observer_unhealthy': 242, 'observer_unhealthy': 2}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 16, 'micro_missing+micro_not_ready+state_insufficient': 21, 'micro_missing+observer_unhealthy': 21, 'observer_unhealthy': 1, 'micro_not_ready+state_insufficient': 1}`
- stale_missing_group_counts: `{'holding': 8, 'exit': 8, 'entry': 1318, 'other': 10, 'scale_in': 1}`
- stale_missing_group_unique_record_counts: `{'exit': 6, 'entry': 21, 'other': 6, 'scale_in': 1, 'holding': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 444, 'observer_unhealthy_with_other_reason': 442, 'observer_unhealthy_only': 2}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `119`
- sequence_fact_broker_order_forbidden_true: `119`
- ofi_qi_fact_actual_order_submitted_false: `8917`
- ofi_qi_fact_broker_order_forbidden_true: `8917`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 98, 'sim_equal_weight': 20, 'real_order_event': 8, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 4472, 'swing_entry_lifecycle_policy_baseline_prior_features': 3634, 'sim_equal_weight': 753, 'swing_sim_exploration_only': 58}`

## Warnings

- none
