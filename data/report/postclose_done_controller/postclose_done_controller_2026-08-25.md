# Postclose DONE Controller - 2026-08-25

- status: `done`
- final_verifier_status: `warning`
- root_cause: `code_improvement_workorder_source_fingerprint_sha256_mismatch:threshold_cycle_ev,code_improvement_workorder_source_fingerprint_size_mismatch:threshold_cycle_ev,postclose_fail_marker_present,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `refresh_pattern_lab_currentness_audit`
- full_wrapper_rerun_used: `False`
- attempts: `2`
- dry_run: `False`

## Actions
- `refresh_pattern_lab_currentness_audit` status=`success` reason=`wrapper tail repair pattern currentness audit refresh before final EV`
- `refresh_pattern_lab_propagation_audit` status=`success` reason=`wrapper tail repair pattern propagation audit refresh before final EV`
- `refresh_code_improvement_workorder` status=`success` reason=`wrapper tail repair workorder refresh before final EV`
- `refresh_threshold_cycle_ev` status=`success` reason=`wrapper tail repair EV refresh after upstream audits and workorder`
- `refresh_code_improvement_workorder_final` status=`success` reason=`wrapper tail repair final workorder source fingerprint refresh after EV`
- `refresh_runtime_approval_summary` status=`success` reason=`wrapper tail repair runtime summary refresh after EV consumers`
- `refresh_next_stage2_checklist` status=`success` reason=`wrapper tail repair checklist refresh after final workorder consumers`
- `refresh_next_preopen_apply` status=`success` reason=`refresh next PREOPEN apply plan after postclose sim-auto/catalog artifacts`
- `refresh_runtime_apply_gap_audit` status=`success` reason=`runtime apply gap audit refresh after next PREOPEN apply`
- `verify_postclose_chain_pending_done` status=`success` reason=`wrapper-tail repair verifier before DONE reconciliation`
- `tail_repair_done_reconciliation` status=`success` reason=`DONE/status reconciliation after wrapper-tail minimal repair`
- `verify_postclose_chain` status=`success` reason=`refresh verifier status`
- `refresh_tuning_performance_control_tower` status=`success` reason=`wrapper tail repair post-DONE tuning performance control tower`
