# Pattern Lab AI Review - 2026-07-28

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
- final_conclusion_count: `5`
- workorder_count: `4`

## Two-Pass Review

- interpretation_count: `10`
- audit_issues: `[]`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `[]`
- source_context_resolutions: `['scalping_pattern_lab_automation', 'swing_strategy_discovery_ev']`

## Final Conclusions

- `scalping_pattern_lab_automation` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`Source quality contract blocked due to sample_count=0 < sample_floor=20.` source_context_resolution=`resolved_by_classified_source_quality_warning` contract=`pattern_lab_ai_review_classified_source_quality_warning`
- `threshold_cycle_ev` domain=`cross_domain` state=`source_quality_gap` decision=`block_runtime_use` reason=`Source file does not exist.`
- `pattern_lab_propagation_audit` domain=`cross_domain` state=`source_quality_gap` decision=`block_runtime_use` reason=`Source file does not exist.`
- `lifecycle_decision_matrix` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`LDM has warnings and all stage policy entries below sample floor.`
- `lifecycle_bucket_discovery` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`Bucket discovery has source contract drift warning.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_threshold_cycle_ev`: Pattern Lab AI review follow-up: threshold_cycle_ev
- `order_pattern_lab_ai_review_pattern_lab_propagation_audit`: Pattern Lab AI review follow-up: pattern_lab_propagation_audit
- `order_pattern_lab_ai_review_lifecycle_decision_matrix`: Pattern Lab AI review follow-up: lifecycle_decision_matrix
- `order_pattern_lab_ai_review_lifecycle_bucket_discovery`: Pattern Lab AI review follow-up: lifecycle_bucket_discovery
