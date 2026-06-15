# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-15 ~ 2026-06-15

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `96`
- swing_ofi_qi_fact: `32994`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `6413`
- stale_missing_unique_record_count: `13`
- stale_missing_ratio: `0.1944`
- reason_counts: `{'micro_missing': 6411, 'micro_stale': 0, 'observer_unhealthy': 18, 'micro_not_ready': 6413, 'state_insufficient': 6413}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 2, 'micro_missing+micro_not_ready+state_insufficient': 6393, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 12, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 6}`
- stale_missing_group_counts: `{'holding': 2, 'entry': 6404, 'scale_in': 7}`
- stale_missing_group_unique_record_counts: `{'entry': 13, 'scale_in': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 18, 'observer_unhealthy_with_other_reason': 18, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `92`
- sequence_fact_broker_order_forbidden_true: `92`
- ofi_qi_fact_actual_order_submitted_false: `32994`
- ofi_qi_fact_broker_order_forbidden_true: `32994`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 75, 'sim_equal_weight': 17, 'real_order_event': 3, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 16821, 'swing_entry_lifecycle_policy_baseline_prior_features': 16009, 'sim_equal_weight': 154, 'swing_sim_exploration_only': 10}`

## Warnings

- none
