# DeepSeek Swing Pattern Lab - Data Quality Report

## Analysis Window: 2026-06-16 ~ 2026-06-16

## Fact Table Row Counts

- swing_trade_fact: `0`
- swing_lifecycle_funnel_fact: `1`
- swing_sequence_fact: `111`
- swing_ofi_qi_fact: `42582`
- completed_trades: `0`
- valid_profit_trades: `0`

## OFI/QI Quality

- stale_missing_count: `7701`
- stale_missing_unique_record_count: `18`
- stale_missing_ratio: `0.1809`
- reason_counts: `{'micro_missing': 7700, 'micro_stale': 0, 'observer_unhealthy': 25, 'micro_not_ready': 7701, 'state_insufficient': 7701}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 1, 'micro_missing+micro_not_ready+state_insufficient': 7675, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 25}`
- reason_combination_unique_record_counts: `{'micro_missing+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 7}`
- stale_missing_group_counts: `{'holding': 1, 'entry': 7698, 'other': 2}`
- stale_missing_group_unique_record_counts: `{'entry': 18, 'other': 1}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 25, 'observer_unhealthy_with_other_reason': 25, 'observer_unhealthy_only': 0}`

## Sim/Probe Provenance

- trade_fact_actual_order_submitted_false: `0`
- trade_fact_broker_order_forbidden_true: `0`
- sequence_fact_actual_order_submitted_false: `111`
- sequence_fact_broker_order_forbidden_true: `111`
- ofi_qi_fact_actual_order_submitted_false: `42582`
- ofi_qi_fact_broker_order_forbidden_true: `42582`
- trade_fact_decision_authority_counts: `{}`
- sequence_fact_decision_authority_counts: `{'source_quality_only': 89, 'sim_equal_weight': 21, 'probe_observe_only': 1}`
- ofi_qi_fact_decision_authority_counts: `{'source_quality_only': 26927, 'swing_entry_lifecycle_policy_baseline_prior_features': 15469, 'sim_equal_weight': 168, 'swing_sim_exploration_only': 18}`

## Warnings

- none
