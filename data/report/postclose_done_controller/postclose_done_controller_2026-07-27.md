# Postclose DONE Controller - 2026-07-27

- status: `done`
- final_verifier_status: `warning`
- root_cause: `postclose_fail_marker_present,ai_watching_score_smoothing_diagnostic_followup_open,lifecycle_bucket_confirmation_windows_not_target,lifecycle_bucket_discovery_rolling10d_parent_granularity_not_target,lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target,lifecycle_complete_flow_absent_workorder_handoff,lifecycle_join_contract_blocked_workorder_handoff,swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_required_source_only,swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_sim_auto_blocked,swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_fail_closed,swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_source_only,active_or_hypothesis_preopen_handoff_pending,active_or_hypothesis_not_instrumented`
- selected_recovery_action: `verify_postclose_chain_pending_done`
- full_wrapper_rerun_used: `False`
- attempts: `2`
- dry_run: `False`

## Actions
- `verify_postclose_chain_pending_done` status=`success` reason=`wrapper-tail repair verifier before DONE reconciliation`
- `tail_repair_done_reconciliation` status=`success` reason=`DONE/status reconciliation after wrapper-tail minimal repair`
- `verify_postclose_chain` status=`success` reason=`refresh verifier status`
