# Swing Pattern Lab Automation - 2026-07-21

## Summary
- deepseek_lab_available: `True`
- findings_count: `3`
- code_improvement_order_count: `2`
- data_quality_warning_count: `1`
- carryover_warning_count: `0`
- runtime_change: `False`
- decision_authority: `swing_pattern_lab_analysis_workorder_source_only`
- runtime_mutation_allowed: `False`

## Consensus Findings
- `swing_pattern_lab_deepseek_selection_low_candidate_count` route=`attach_existing_family` family=`swing_selection_top_k` stage=`selection`
- `swing_pattern_lab_deepseek_entry_no_submissions` route=`design_family_candidate` family=`-` stage=`entry`
- `swing_pattern_lab_deepseek_holding_exit_no_trades` route=`defer_evidence` family=`-` stage=`holding_exit`

## Code Improvement Orders
- `order_swing_pattern_lab_deepseek_selection_low_candidate_count` Low swing candidate count per day decision=`attach_existing_family` subsystem=`swing_model_selection` runtime_effect=`False`
- `order_swing_pattern_lab_deepseek_entry_no_submissions` All selected candidates failed to reach order submission decision=`design_family_candidate` subsystem=`swing_entry_funnel` runtime_effect=`False`

## OFI/QI Quality
- stale_missing_ratio: `0.0`
- stale_missing_unique_record_count: `0`
- reason_counts: `{}`
- reason_combination_counts: `{}`
- reason_combination_unique_record_counts: `{}`
- stale_missing_group_counts: `{}`
- stale_missing_group_unique_record_counts: `{}`
- observer_unhealthy_overlap: `{'observer_unhealthy_total': 0, 'observer_unhealthy_with_other_reason': 0, 'observer_unhealthy_only': 0}`
- source_quality_blocked_families: `[]`
