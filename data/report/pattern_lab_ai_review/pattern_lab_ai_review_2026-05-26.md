# Pattern Lab AI Review - 2026-05-26

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- decision_authority: `pattern_lab_ai_review_source_only`
- ai_two_pass_review_status: `parsed`
- provider: `openai`
- model: `gpt-5.4`
- fallback_used: `False`
- audit_status: `correction_required`
- final_conclusion_count: `4`
- workorder_count: `4`

## Two-Pass Review

- interpretation_count: `4`
- audit_issues: `['pattern_lab_currentness_audit is warning with fail_count=2 and missing_feedback_source_count=3.', 'threshold_cycle_ev source is absent in the provided bundle.', 'Scalping re-entry feedback wiring is missing for threshold/LDM/bucket sources.', 'Swing re-entry feedback wiring is missing for threshold/LDM/bucket/discovery sources.', 'Swing OFI/QI source quality is degraded by high stale or missing coverage.', 'Swing lifecycle bucket discovery AI review augmentation is not fully configured.']`
- forbidden_use_violations: `[]`

## Final Conclusions

- `scalping_reentry_feedback_missing` domain=`scalping` state=`automation_handoff_gap` decision=`surface_workorder` reason=`Scalping pattern-lab output is fresh enough for source collection, but it is missing required re-entry feedback from threshold and lifecycle sources.`
- `swing_reentry_feedback_missing` domain=`swing` state=`automation_handoff_gap` decision=`surface_workorder` reason=`Swing pattern-lab output is missing required re-entry feedback wiring from threshold, swing lifecycle, and swing discovery sources.`
- `swing_ofi_qi_source_quality_gap` domain=`swing` state=`source_quality_gap` decision=`surface_workorder` reason=`The swing lab has an explicit microstructure source-quality problem, with OFI/QI missing or stale on most evaluated rows.`
- `swing_ai_review_config_gap` domain=`swing` state=`ai_review_gap` decision=`surface_workorder` reason=`Swing lifecycle bucket discovery indicates AI review is needed but not fully configured for that path.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_scalping_reentry_feedback_missing`: Pattern Lab AI review follow-up: scalping_reentry_feedback_missing
- `order_pattern_lab_ai_review_swing_reentry_feedback_missing`: Pattern Lab AI review follow-up: swing_reentry_feedback_missing
- `order_pattern_lab_ai_review_swing_ofi_qi_source_quality_gap`: Pattern Lab AI review follow-up: swing_ofi_qi_source_quality_gap
- `order_pattern_lab_ai_review_swing_ai_review_config_gap`: Pattern Lab AI review follow-up: swing_ai_review_config_gap
