# Plan Rebase Daily Renewal - 2026-05-20

- mode: `bounded_document_mutation_queue`
- runtime_mutation_allowed: `False`
- document_mutation_allowed: `True`
- document_mutation_execution_allowed: `True`
- document_mutation_authority: `bounded_downstream_document_worker`
- document_mutation_self_apply: `False`
- document_mutation_phase: `postclose_downstream_after_runtime_summary`
- renewal_state: `proposal_ready`
- selected_runtime_families: `soft_stop_whipsaw_confirmation, latency_classifier_runtime_profile, scalp_sim_candidate_window_expansion, scalp_sim_ai_budget_manager, lifecycle_decision_matrix_runtime`

## Document Update Queue

- `README family`: `project_overview_and_artifact_contract` (/home/ubuntu/KORStockScan/README.md, /home/ubuntu/KORStockScan/docs/README.md, /home/ubuntu/KORStockScan/data/threshold_cycle/README.md, /home/ubuntu/KORStockScan/data/report/README.md)
- `runbook`: `time_based_operations_and_postclose_review_steps` (/home/ubuntu/KORStockScan/docs/time-based-operations-runbook.md)
- `Plan Rebase`: `current_principles_and_active_open_snapshot` (/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.rebase.md)
- `prompt`: `session_entry_pointer_and_source_of_truth_map` (/home/ubuntu/KORStockScan/docs/plan-korStockScanPerformanceOptimization.prompt.md)
- `AGENTS`: `working_instruction_snapshot` (/home/ubuntu/KORStockScan/AGENTS.md)

## Mutation Passes

- `pass1_bounded_update`: 1차 수정(first-pass bounded update) / target document updates are drafted within allowed_update_scope only
- `pass2_audit_review`: 2차 감리(second-pass audit review) / history archiving, Korean/English abbreviation notation, runtime mutation guardrails, and parser validation are reviewed
- `finalize_after_pass2`: 최종 수정(finalize after second-pass review) / only pass2 findings are amended before the document mutation is closed

## Proposed Snapshot

- basis_date: `2026-05-20 KST`
- runtime_change: `True`
- openai_decision: `keep_ws`
- swing_requested/approved: `0` / `0`
- panic_approval_requested: `0`

## Guardrails

- allowed_update_scope: `readme_project_and_artifact_contract_summary, runbook_postclose_review_contract, plan_rebase_current_date, plan_rebase_current_runtime_state_summary, prompt_source_of_truth_summary, agents_current_state_snapshot`
- forbidden_update_scope: `metric_decision_contract, rollback_guard_relaxation, live_or_real_order_approval, runtime_threshold_mutation, archive_deletion`
- archive_history_before_mutation: `True`
- abbreviation_policy: `first_use_korean_english_parallel_notation`
