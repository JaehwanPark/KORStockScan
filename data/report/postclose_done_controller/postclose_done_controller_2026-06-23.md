# Postclose DONE Controller - 2026-06-23

- status: `blocked_recoverable_action_failed`
- final_verifier_status: `fail`
- root_cause: `threshold_cycle_ev_stale_before_code_improvement_workorder,threshold_cycle_ev_stale_before_pattern_lab_ai_review,runtime_approval_summary_stale_before_pattern_lab_ai_review,active_sim_priority_preopen_handoff_pending,ai_watching_score_smoothing_diagnostic_followup_open,lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target,swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_required_source_only,swing_lifecycle_bucket_discovery:ai_two_pass_review_followup_sim_auto_blocked,swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_fail_closed,swing_lifecycle_bucket_discovery:ai_two_pass_review_partial_source_only,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `refresh_daily_threshold_cycle_report`
- full_wrapper_rerun_used: `False`
- attempts: `1`
- dry_run: `False`

## Actions
- `refresh_daily_threshold_cycle_report` status=`success` reason=`daily report refresh before EV/workorder repair`
- `refresh_threshold_cycle_ev` status=`success` reason=`threshold EV source refresh before downstream consumers`
- `refresh_pattern_lab_currentness_audit` status=`success` reason=`pattern currentness audit refresh after EV`
- `refresh_pattern_lab_propagation_audit` status=`success` reason=`pattern propagation audit refresh after EV`
- `refresh_code_improvement_workorder` status=`success` reason=`workorder lineage repair after EV and pattern consumers`
- `refresh_runtime_approval_summary` status=`success` reason=`runtime summary refresh after EV consumer repair`
- `refresh_next_preopen_apply` status=`success` reason=`refresh next PREOPEN apply plan after postclose sim-auto/catalog artifacts`
- `refresh_runtime_apply_gap_audit` status=`success` reason=`runtime apply gap audit refresh after next PREOPEN apply`
- `verify_postclose_chain` status=`failed` reason=`refresh verifier status`

## Blocked Reasons
- `verify_postclose_chain_failed`
