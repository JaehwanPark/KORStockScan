# Postclose DONE Controller - 2026-06-16

- status: `done`
- final_verifier_status: `warning`
- root_cause: `postclose_fail_marker_present,active_sim_priority_preopen_handoff_pending,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `refresh_threshold_cycle_ev`
- full_wrapper_rerun_used: `False`
- attempts: `2`
- dry_run: `False`

## Actions
- `refresh_threshold_cycle_ev` status=`success` reason=`wrapper tail repair EV refresh after post-conversion workorder`
- `refresh_runtime_approval_summary` status=`success` reason=`wrapper tail repair runtime summary refresh after EV`
- `verify_postclose_chain_pending_done` status=`success` reason=`wrapper-tail repair verifier before DONE reconciliation`
- `tail_repair_done_reconciliation` status=`success` reason=`DONE/status reconciliation after wrapper-tail minimal repair`
- `verify_postclose_chain` status=`success` reason=`refresh verifier status`
- `refresh_tuning_performance_control_tower` status=`success` reason=`wrapper tail repair post-DONE tuning performance control tower`
