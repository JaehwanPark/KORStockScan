# Pattern Lab AI Review - 2026-07-29

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `pattern_lab_ai_review_source_only`
- ai_two_pass_review_status: `parsed`
- provider: `openai`
- model: `qwen.qwen3-235b-a22b-2507-v1:0`
- fallback_used: `False`
- audit_status: `correction_required`
- final_conclusion_count: `6`
- workorder_count: `1`

## Two-Pass Review

- interpretation_count: `6`
- audit_issues: `[]`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `[]`
- source_context_resolutions: `['scalp_entry_adm_sample_floor_gap', 'lifecycle_bucket_discovery_source_contract_drift']`

## Final Conclusions

- `scalp_entry_adm_sample_floor_gap` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`Joined sample size (3) is below required floor (20). Source cannot be used for runtime decisions.` source_context_resolution=`resolved_by_existing_sample_floor_hold_contract` contract=`scalp_entry_adm_pattern_lab_source_quality`
- `missing_threshold_cycle_ev_source` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`threshold_cycle_ev source is missing, breaking the LDM/threshold feedback loop required for adaptive tuning.`
- `missing_code_improvement_workorder_source` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`code_improvement_workorder source is missing, preventing closure of code-level improvement feedback loop.`
- `missing_pattern_lab_propagation_audit` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`pattern_lab_propagation_audit source is missing, indicating incomplete propagation audit for pattern lab outputs.`
- `lifecycle_bucket_discovery_source_contract_drift` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`lifecycle_bucket_discovery reports source_contract_drift_warning, indicating potential schema or policy misalignment.` source_context_resolution=`resolved_by_classified_source_quality_warning` contract=`pattern_lab_ai_review_classified_source_quality_warning`
- `lifecycle_bucket_discovery_automation_handoff_gap` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`lifecycle_bucket_discovery contains 1 automation_handoff_gap, indicating a candidate not consumable by downstream systems.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_lifecycle_bucket_discovery_automation_handoff_gap`: Pattern Lab AI review follow-up: lifecycle_bucket_discovery_automation_handoff_gap
