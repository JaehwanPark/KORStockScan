# Swing Pattern Lab Automation - 2026-06-08

## Summary
- deepseek_lab_available: `True`
- findings_count: `5`
- code_improvement_order_count: `4`
- data_quality_warning_count: `1`
- carryover_warning_count: `0`
- runtime_change: `False`
- decision_authority: `swing_pattern_lab_analysis_workorder_source_only`
- runtime_mutation_allowed: `False`

## Consensus Findings
- `swing_pattern_lab_deepseek_entry_no_submissions` route=`design_family_candidate` family=`-` stage=`entry`
- `swing_pattern_lab_deepseek_holding_exit_no_trades` route=`defer_evidence` family=`-` stage=`holding_exit`
- `swing_pattern_lab_deepseek_scale_in_events_observed` route=`attach_existing_family` family=`swing_scale_in_ofi_qi_confirmation` stage=`scale_in`
- `swing_pattern_lab_deepseek_ofi_qi_stale_missing` route=`implement_now` family=`swing_entry_ofi_qi_execution_quality` stage=`ofi_qi`
- `swing_pattern_lab_deepseek_ofi_qi_smoothing_review` route=`attach_existing_family` family=`swing_exit_ofi_qi_smoothing` stage=`ofi_qi`

## Code Improvement Orders
- `order_swing_pattern_lab_deepseek_entry_no_submissions` All selected candidates failed to reach order submission decision=`design_family_candidate` subsystem=`swing_entry_funnel` runtime_effect=`False`
- `order_swing_pattern_lab_deepseek_scale_in_events_observed` Scale-in events observed for swing positions decision=`attach_existing_family` subsystem=`swing_scale_in` runtime_effect=`False`
- `order_swing_pattern_lab_deepseek_ofi_qi_stale_missing` OFI/QI stale/missing quality review decision=`implement_now` subsystem=`swing_micro_context` runtime_effect=`False`
- `order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review` OFI/QI exit smoothing action distribution decision=`attach_existing_family` subsystem=`swing_micro_context` runtime_effect=`False`

## OFI/QI Quality
- stale_missing_ratio: `0.6002`
- stale_missing_unique_record_count: `23`
- reason_counts: `{'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}`
- reason_combination_counts: `{'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}`
- reason_combination_unique_record_counts: `{'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}`
- stale_missing_group_counts: `{'holding': 9, 'scale_in': 39, 'entry': 16232, 'other': 4}`
- stale_missing_group_unique_record_counts: `{'scale_in': 2, 'entry': 22, 'other': 2}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[{'family': 'swing_entry_ofi_qi_execution_quality', 'stage': 'entry', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['entry_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 22, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}, 'reason_counts': {'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}, {'family': 'swing_scale_in_ofi_qi_confirmation', 'stage': 'scale_in', 'metric_role': 'source_quality_gate', 'decision_authority': 'swing_pattern_lab_analysis_workorder_source_only', 'window_policy': 'same_day_pattern_lab_source_quality', 'sample_floor': 1, 'primary_decision_metric': 'source_quality_gate', 'source_quality_gate': 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded', 'source_contract_version': 'swing_micro_context_source_quality_v1', 'source_contract_status': 'implemented', 'source_quality_blockers': ['scale_in_ofi_qi_invalid_micro_context'], 'invalid_micro_context_unique_record_count': 2, 'invalid_reason_combination_unique_record_counts': {'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 18, 'micro_missing+observer_unhealthy': 1, 'micro_missing+micro_not_ready+state_insufficient': 22}, 'reason_counts': {'micro_missing': 16275, 'micro_stale': 0, 'observer_unhealthy': 3563, 'micro_not_ready': 16249, 'state_insufficient': 16249}, 'reason_combination_counts': {'micro_not_ready+state_insufficient': 9, 'micro_missing+observer_unhealthy+micro_not_ready+state_insufficient': 3528, 'micro_missing+observer_unhealthy': 35, 'micro_missing+micro_not_ready+state_insufficient': 12712}, 'observer_unhealthy_overlap': {'observer_unhealthy_total': 3563, 'observer_unhealthy_with_other_reason': 3563, 'observer_unhealthy_only': 0}, 'automation_input': True, 'runtime_effect': False, 'allowed_runtime_apply': False, 'forbidden_uses': ['swing_real_order_enable', 'one_share_real_canary', 'scale_in_real_canary', 'runtime_threshold_mutation', 'provider_route_change', 'bot_restart', 'recommendation_history_replace']}]`
