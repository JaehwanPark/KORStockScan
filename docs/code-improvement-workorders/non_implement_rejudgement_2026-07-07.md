# 2026-07-07 Non-Implement Rejudgement

- source_workorder: `docs/code-improvement-workorders/code_improvement_workorder_2026-07-07.md`
- source_json: `data/report/code_improvement_workorder/code_improvement_workorder_2026-07-07.json`
- checked_at_kst: `2026-07-07T20:49:54+09:00`
- scope: selected non-implement orders, longstanding non-implement orders, and root-cause-open implemented handoffs
- runtime_effect: `false`
- allowed_runtime_apply: `false`

## Decision

No additional `implement_now` order is opened by this rejudgement.

The regenerated workorder has `selected_implement_now_new_runtime_effect_false_count=0`,
`selected_unimplemented_runtime_effect_false_count=0`, and
`needs_followup_workorder_count=0`. Selected non-implement items remain report-only,
source-quality, provenance, or evidence-collection surfaces.

## Selected Non-Implement Summary

- selected_order_count: `108`
- selected_decision_counts: `attach_existing_family=106`, `defer_evidence=2`
- selected_runtime_effect_false_count: `108`
- selected_terminal_non_implement_runtime_effect_false_count: `7`
- selected_longstanding_non_implement_disposition_counts: `keep_visible_by_design=5`, `review_required=2`
- selected_longstanding_non_implement_action_required_order_ids: `[]`

## Rejudgement By Disposition

### Keep Visible By Design

These 5 longstanding items are intentionally visible because they are rollup or
source-quality evidence, not missing runtime implementation:

- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_d982edbd`
  - reason: exit-stage child bucket evidence, terminal not-applicable evidence
  - handling: keep as source-quality visibility until lifecycle flow confirmation or explicit not-applicable labeling closes the bucket
- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_overnight_sell_today_rule_scalp_sim_overnight_sell_tod_ff77f4c9`
  - reason: exit-stage child bucket evidence, terminal not-applicable evidence
  - handling: keep as source-quality visibility until lifecycle flow confirmation or explicit not-applicable labeling closes the bucket
- `order_lifecycle_quiet_gap_ai_review_coverage_rollup`
  - reason: quiet-gap rollup and low AI-review coverage evidence
  - handling: keep visible; no runtime implementation until rollup produces a concrete source-quality or report-provenance defect
- `order_lifecycle_quiet_gap_positive_source_only_rollup`
  - reason: positive source-only quiet-gap rollup
  - handling: keep visible as source-only evidence; no runtime implementation
- `order_lifecycle_source_dimension_gap_rollup`
  - reason: lifecycle source dimension rollup evidence
  - handling: keep visible; resolve only through explicit lifecycle source labeling or join-quality improvements

### Review Required

These 2 longstanding items remain deferred evidence, but the repeated unresolved
cause is now classified as a lifecycle label/join gap rather than a runtime
threshold or order-path defect:

- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_euphoria_context_noop_rule_exit_rule_unknown_outcome_o_5f592cef`
  - observed evidence: `source=scalp_sim_euphoria_context_noop`, `rule=exit_rule_unknown`, `outcome=outcome_unknown`, `profit=profit_unknown`
  - workorder provenance: `recommended_resolution=join_labels_before_bucket_decision`, `unknown_reason_counts={'join_gap': 3}`
  - handling: keep deferred; next implementation candidate is LDM exit bucket label/join enrichment that binds panic/euphoria source events to explicit exit outcome and profit labels before bucket decision
- `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_panic_context_warning_rule_exit_rule_unknown_outcome_o_58a13326`
  - observed evidence: `source=scalp_sim_panic_context_warning`, `rule=exit_rule_unknown`, `outcome=outcome_unknown`, `profit=profit_unknown`
  - workorder provenance: `recommended_resolution=join_labels_before_bucket_decision`, `unknown_reason_counts={'join_gap': 3}`
  - handling: keep deferred; next implementation candidate is the same LDM exit bucket label/join enrichment, with no runtime effect and no broker/order/provider change

## Longstanding Root-Cause-Open Handoffs

- handoff_closed_root_cause_open_count: `20`
- source_report_type: `conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- implementation_status: `implemented`
- root_cause_signal: `null`

Rejudgement: do not reopen these as immediate implementation work. They are
implemented conversion-lane handoffs whose root-cause closure still depends on
subsequent evidence and conversion-lane attribution. Keep them visible, but do
not promote them to runtime work without a new concrete source-quality,
report-provenance, or conversion-lane acceptance failure.

## Acceptance

- Current workorder still has no selected runtime-effect implementation target.
- Longstanding `review_required` items have a concrete next handling path:
  LDM exit bucket label/join enrichment, source/report only.
- No provider, bot process, threshold, cap, broker/order, hard safety, or
  runtime authority change is authorized by this rejudgement.
