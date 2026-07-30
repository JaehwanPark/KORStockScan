# Pattern Lab AI Review - 2026-07-30

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `pattern_lab_ai_review_source_only`
- ai_two_pass_review_status: `parsed`
- provider: `openai`
- model: `qwen.qwen3-235b-a22b-2507-v1:0`
- fallback_used: `False`
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

- `scalp_entry_adm_sample_floor_below` domain=`scalping` state=`source_quality_gap` decision=`block_runtime_use` reason=`Source quality contract explicitly blocks use due to joined_sample_below_sample_floor. No LDM/threshold feedback available to override. This is a deterministic source-quality gate.`
- `sim_auto_nonpositive_ev_present` domain=`scalping` state=`source_quality_gap` decision=`block_runtime_use` reason=`Negative EV bucket candidate detected in lifecycle_bucket_discovery. Must be reviewed and resolved before any runtime consideration. No threshold feedback available to override.`
- `ai_two_pass_review_incomplete` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`AI two-pass review is incomplete (4/5 shards parsed). This constitutes an automation handoff gap as per lifecycle_bucket_discovery summary. Full review completion is required before downstream use.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_scalp_entry_adm_sample_floor_below`: Pattern Lab AI review follow-up: scalp_entry_adm_sample_floor_below
- `order_pattern_lab_ai_review_sim_auto_nonpositive_ev_present`: Pattern Lab AI review follow-up: sim_auto_nonpositive_ev_present
- `order_pattern_lab_ai_review_ai_two_pass_review_incomplete`: Pattern Lab AI review follow-up: ai_two_pass_review_incomplete
