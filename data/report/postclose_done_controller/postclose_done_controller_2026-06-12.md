# Postclose DONE Controller - 2026-06-12

- status: `blocked_structural_contract_gap`
- final_verifier_status: `fail`
- root_cause: `active_sim_priority_handoff_missing,ai_correction_unavailable_blocks_runtime_candidates,postclose_fail_marker_present,active_or_hypothesis_preopen_handoff_pending`
- selected_recovery_action: `refresh_threshold_cycle_ev`
- full_wrapper_rerun_used: `False`
- attempts: `1`
- dry_run: `False`

## Actions
- `refresh_threshold_cycle_ev` status=`success` reason=`wrapper tail repair EV refresh after post-conversion workorder`
- `refresh_runtime_approval_summary` status=`success` reason=`wrapper tail repair runtime summary refresh after EV`
- `verify_postclose_chain_pending_done` status=`failed` reason=`wrapper-tail repair verifier before DONE reconciliation`

## Blocked Reasons
- `verify_postclose_chain_pending_done_failed`

## Structural Blockers
- `requires_policy_lineage_fix:active_sim_priority_inactive_key_consumed`
- `requires_policy_lineage_fix:active_sim_priority_handoff_missing`
- requires_code_fix: `False`
- requires_policy_lineage_fix: `True`

## Structural Next Actions
- `fix_active_sim_priority_seed_lineage_and_verify_no_inactive_runtime_key`
