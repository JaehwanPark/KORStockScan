# Stage Hook Workorder Discovery - 2026-06-29

## Summary

- status: `warning`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- candidates: `6`
- workorders: `2`
- ai_two_pass_review_status: `parsed`
- audit_status: `pass`
- readiness_tier_counts: `{'observe_only': 1, 'producer_needed': 2, 'blocked_by_source_quality': 1, 'implementation_workorder_ready': 2}`

## Candidates

### `stage_hook_submit_reprice_fill_quality_probe`
- hook_name: `submit_reprice_fill_quality_probe`
- hook_class: `submit_quality_hook_candidate`
- stage: `submit`
- readiness_tier: `observe_only`
- evidence_score: `28.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`

### `stage_hook_scale_in_would_add_policy_probe`
- hook_name: `scale_in_would_add_policy_probe`
- hook_class: `scale_in_policy_hook_candidate`
- stage: `scale_in`
- readiness_tier: `producer_needed`
- evidence_score: `44.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`

### `stage_hook_entry_policy_exception_router_candidate`
- hook_name: `entry_policy_exception_router_candidate`
- hook_class: `entry_policy_hook_candidate`
- stage: `entry`
- readiness_tier: `blocked_by_source_quality`
- evidence_score: `11.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`

### `stage_hook_holding_flow_runner_debounce_guard`
- hook_name: `holding_flow_runner_debounce_guard`
- hook_class: `runtime_arbitration_hook`
- stage: `holding`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`

### `stage_hook_plateau_breakdown_exit_arbitration_probe`
- hook_name: `plateau_breakdown_exit_arbitration_probe`
- hook_class: `runtime_arbitration_hook`
- stage: `exit`
- readiness_tier: `implementation_workorder_ready`
- evidence_score: `100.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`

### `stage_hook_stop_recovery_review_probe`
- hook_name: `stop_recovery_review_probe`
- hook_class: `runtime_arbitration_hook`
- stage: `exit`
- readiness_tier: `producer_needed`
- evidence_score: `51.0`
- forbidden_uses: `account guard bypass, bot restart, broker guard bypass, broker order submit, cooldown guard bypass, emergency stop override, entry decision override, exit decision override, hard stop override, order guard bypass, position cap release, protect stop override, provider change, quantity guard bypass, real order enablement, threshold mutation, real_1share_as_preapply_primary_ev, real_one_share_as_preapply_primary_ev, merge_real_pnl_with_sim_probe_ev, runtime_change_from_preapply_real_sample`
