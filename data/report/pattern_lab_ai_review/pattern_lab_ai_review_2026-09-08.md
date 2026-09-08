# Pattern Lab AI Review - 2026-09-08

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
- material_review_current: `True`
- review_reentry: `{'schema': 'pattern_review_reentry_v1', 'date': '2026-09-08', 'state': 'reviewed', 'attempt_limit': 2, 'attempts_used': 2, 'remaining_attempts': 0, 'attempted_material_hashes': ['0e20d0fd83231e1313ca4e42897785bd171cc8cb5117ebd8fbea12ec87a1f75a', 'f6dbfcaa0c9e620d866e2dc1d56f7f132c67d8c189affc7207a1107630d98dd7'], 'new_provider_calls': 0, 'runtime_effect': False, 'allowed_runtime_apply': False}`
- original_ai_input_context_hash: `a5f8e10616f6c86154d244bc4dbde41e1b662a9c372cb6de717967f398b50dc6`
- reconciled_source_context_hash: `6255d46e02e6ecb929afc5557ea283a0586e68c83aa4065a73fa58eea1ab4d20`
- audit_status: `pass`
- final_conclusion_count: `3`
- workorder_count: `3`

## Two-Pass Review

- interpretation_count: `3`
- audit_issues: `[]`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `[]`
- source_context_resolutions: `[]`

## Final Conclusions

- `currentness:claude_small_net_generation_contract` domain=`scalping` state=`source_quality_gap` decision=`surface_workorder` reason=`Source quality gap confirmed by AI review follow-up. Requires new evidence collection and re-run of owning verifier.`
- `currentness:pattern_lab_ai_review_contract` domain=`scalping` state=`source_quality_gap` decision=`surface_workorder` reason=`Source quality gap confirmed by AI review follow-up. Requires new evidence collection and re-run of owning verifier.`
- `currentness:scalping_ldm_threshold_reentry_sources` domain=`scalping` state=`automation_handoff_gap` decision=`surface_workorder` reason=`Retired ADM/LDM sources are not required. threshold_cycle_ev is active re-entry source. Gap is informational; no action required beyond documentation.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_currentness_claude_small_net_generation_contract`: Pattern Lab AI review follow-up: currentness:claude_small_net_generation_contract
- `order_pattern_lab_ai_review_currentness_pattern_lab_ai_review_contract`: Pattern Lab AI review follow-up: currentness:pattern_lab_ai_review_contract
- `order_pattern_lab_ai_review_currentness_scalping_ldm_threshold_reentry_sources`: Pattern Lab AI review follow-up: currentness:scalping_ldm_threshold_reentry_sources
