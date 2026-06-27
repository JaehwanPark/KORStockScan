# Pattern Lab AI Review - 2026-06-26

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
- final_conclusion_count: `2`
- workorder_count: `1`

## Two-Pass Review

- interpretation_count: `2`
- audit_issues: `['ai_review_gap', 'automation_handoff_gap']`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `[]`
- source_context_resolutions: `[]`

## Final Conclusions

- `ai_review_gap` domain=`scalping` state=`source_only_keep_collecting` decision=`keep` reason=`Missing AI review contract prevents feedback integration from LDM/threshold_cycle_ev, violating pattern_lab_ai_review_contract currentness check`
- `automation_handoff_gap` domain=`swing` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`19 sim_auto candidates downgraded due to missing AI review; ai_two_pass_review_status=missing despite deterministic proposals present`

## Code Improvement Orders

- `order_pattern_lab_ai_review_automation_handoff_gap`: Pattern Lab AI review follow-up: automation_handoff_gap
