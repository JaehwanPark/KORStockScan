# Postclose DONE Controller - 2026-08-25

- status: `done`
- final_verifier_status: `warning`
- root_cause: `code_improvement_workorder_source_fingerprint_sha256_mismatch:threshold_cycle_calibration,code_improvement_workorder_source_fingerprint_sha256_mismatch:threshold_cycle_ev,code_improvement_workorder_source_fingerprint_size_mismatch:threshold_cycle_calibration,code_improvement_workorder_source_fingerprint_size_mismatch:threshold_cycle_ev,runtime_approval_summary_stale_before_threshold_cycle_ev,runtime_approval_summary_stale_before_threshold_cycle_ai_review,runtime_approval_summary_stale_before_threshold_cycle_calibration,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `refresh_threshold_cycle_ev`
- full_wrapper_rerun_used: `False`
- attempts: `2`
- dry_run: `False`

## Actions
- `refresh_threshold_cycle_ev` status=`success` reason=`downstream EV source refresh`
- `refresh_code_improvement_workorder` status=`success` reason=`final workorder fingerprint refresh after EV`
- `refresh_runtime_approval_summary` status=`success` reason=`runtime summary source refresh after EV and workorder`
