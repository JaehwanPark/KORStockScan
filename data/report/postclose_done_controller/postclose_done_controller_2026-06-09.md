# Postclose DONE Controller - 2026-06-09

- status: `done`
- final_verifier_status: `warning`
- root_cause: `postclose_fail_marker_present,active_sim_priority_preopen_handoff_pending,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `verify_postclose_chain_pending_done`
- full_wrapper_rerun_used: `False`
- attempts: `2`
- dry_run: `False`

## Actions
- `verify_postclose_chain_pending_done` status=`success` reason=`wrapper-tail repair verifier before DONE reconciliation`
- `tail_repair_done_reconciliation` status=`success` reason=`DONE/status reconciliation after wrapper-tail minimal repair`
- `verify_postclose_chain` status=`success` reason=`refresh verifier status`
