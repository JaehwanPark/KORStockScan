# Pattern Lab AI Review - 2026-06-22

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

- interpretation_count: `5`
- audit_issues: `[]`
- forbidden_use_violations: `[]`
- source_contract_resolutions: `['swing_micro_context_source_quality']`
- source_context_resolutions: `[]`

## Final Conclusions

- `swing_micro_context_source_quality` domain=`swing` state=`source_only_keep_collecting` decision=`keep` reason=`Source quality gate 'swing_orderbook_micro_context_ready_or_blocker_provenance_recorded' is not passing due to 42 stale/missing micro-context records. Runtime use is blocked until source quality is restored.` source_contract_resolution=`resolved_by_implemented_source_contract` contract=`swing_micro_context_source_quality`
- `swing_lifecycle_bucket_discovery_ai_two_pass_partial` domain=`swing` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`AI two-pass review is incomplete (status=partial) and followup is required, which blocks sim_auto approval. Runtime handoff is blocked until AI review is completed and followup resolved.`
- `threshold_cycle_ev_sim_evidence_no_live` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`Sim evidence is present but no live bucket is ready (live_auto_ready_count=0). This represents a handoff gap from simulation to live execution. Runtime use is blocked until live bucket readiness is established.`
- `lifecycle_bucket_discovery_source_contract_drift` domain=`scalping` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`Source contract drift detected (source_contract_status=warning). This creates uncertainty in the handoff process. Runtime use is blocked until contract drift is resolved.`
- `swing_strategy_discovery_pending_future_quotes` domain=`swing` state=`automation_handoff_gap` decision=`block_runtime_use` reason=`A large number of arms (4315) have pending future quotes, preventing final labeling and evidence closure. Runtime handoff is blocked until label status is complete.`

## Code Improvement Orders

- `order_pattern_lab_ai_review_swing_lifecycle_bucket_discovery_ai_two_pass_partial`: Pattern Lab AI review follow-up: swing_lifecycle_bucket_discovery_ai_two_pass_partial
- `order_pattern_lab_ai_review_threshold_cycle_ev_sim_evidence_no_live`: Pattern Lab AI review follow-up: threshold_cycle_ev_sim_evidence_no_live
- `order_pattern_lab_ai_review_lifecycle_bucket_discovery_source_contract_drift`: Pattern Lab AI review follow-up: lifecycle_bucket_discovery_source_contract_drift
- `order_pattern_lab_ai_review_swing_strategy_discovery_pending_future_quotes`: Pattern Lab AI review follow-up: swing_strategy_discovery_pending_future_quotes
