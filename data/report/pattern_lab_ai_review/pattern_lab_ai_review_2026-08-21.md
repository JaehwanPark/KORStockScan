# Pattern Lab AI Review - 2026-08-21

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `pattern_lab_ai_review_source_only`
- ai_two_pass_review_status: `parsed`
- provider: `bedrock_qwen3`
- model: `qwen.qwen3-235b-a22b-2507-v1:0`
- configured_primary_provider/model: `bedrock_qwen3` / `qwen.qwen3-235b-a22b-2507-v1:0`
- response_reused/new_provider_call: `True` / `False`
- fallback_used: `False`
- audit_status: `correction_required`
- final_conclusion_count: `4`
- workorder_count: `1`

## Two-Pass Review

- interpretation_count: `5`
- audit_issues: `[]`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `[]`
- source_context_resolutions: `['scalping_pattern_lab_automation']`

## Final Conclusions

- `scalping_pattern_lab_automation` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`scalp_entry_adm source_quality_contract blocked due to joined_sample_below_sample_floor (10/20). tuning_input_allowed=false. Cannot proceed without sample floor met.` source_context_resolution=`resolved_by_classified_source_quality_warning` contract=`pattern_lab_ai_review_classified_source_quality_warning`
- `threshold_cycle_ev` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`Deterministic feedback-source reconciliation superseded the provider gap assertion (resolved_by_existing_feedback_source_context).`
- `pattern_lab_propagation_audit` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`Deterministic feedback-source reconciliation superseded the provider gap assertion (resolved_by_existing_feedback_source_context).`
- `lifecycle_decision_matrix` domain=`scalping` state=`source_quality_gap` decision=`block_runtime_use` reason=`source_quality_preflight_gate excluded 263 rows due to field gaps (e.g., minute_candle_window_fresh_contract) and invalid labels. This indicates upstream instrumentation and labeling defects that degrade source quality.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_lifecycle_decision_matrix`: Pattern Lab AI review follow-up: lifecycle_decision_matrix
