# Postclose DONE Controller - 2026-09-14

- status: `done`
- final_verifier_status: `warning`
- root_cause: `postclose_summary_handoff:tower:source_generation_mismatch,postclose_summary_handoff:tower:intake_semantics_mismatch,postclose_summary_handoff:checklist:source_generation_mismatch,postclose_summary_handoff:checklist:intake_semantics_mismatch,limit_down_watch_ordered_path_not_observed,microstructure_diagnostic:warning`
- selected_recovery_action: `verify_pre_summary_chain`
- full_wrapper_rerun_used: `False`
- machine_entry_timing_source_date_quarantined: `False`
- machine_entry_timing_quarantine_next_action: `None`
- attempts: `2`
- dry_run: `False`

## Actions
- `verify_pre_summary_chain` status=`success` reason=`refresh verifier status`
- `refresh_tuning_performance_control_tower` status=`success` reason=`wrapper tail repair post-DONE tuning performance control tower`
- `refresh_next_stage2_checklist` status=`success` reason=`final source generation handoff after summary recovery`
- `verify_postclose_chain` status=`success` reason=`refresh verifier status`
