# Automation Chain Trigger Decision 2026-06-12

- scope: `all`
- run_count: `13`
- skip_count: `2`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Decisions

| step | decision | reasons |
| --- | --- | --- |
| `lifecycle_window_rolling5d` | `run` | output_missing_or_unreadable, output_non_reusable_status, source_missing_or_unreadable |
| `lifecycle_window_rolling10d` | `run` | output_missing_or_unreadable, output_non_reusable_status, source_missing_or_unreadable |
| `lifecycle_window_mtd` | `run` | output_missing_or_unreadable, output_non_reusable_status, source_missing_or_unreadable |
| `scalp_sim_ai_deferred_review` | `skip` | fresh_outputs_no_trigger |
| `pattern_lab_currentness_audit` | `run` | upstream_drift_signal |
| `pattern_lab_ai_review` | `run` | upstream_drift_signal |
| `observation_source_quality_audit` | `run` | source_missing_or_unreadable |
| `observation_source_quality_backfill_audit` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `codebase_performance_workorder` | `skip` | fresh_outputs_no_trigger |
| `producer_gap_discovery` | `run` | upstream_drift_signal |
| `stage_hook_workorder_discovery` | `run` | upstream_drift_signal |
| `stage_hook_runtime_scaffold` | `run` | upstream_drift_signal |
| `pattern_lab_propagation_audit` | `run` | upstream_drift_signal |
| `runtime_apply_gap_audit` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `workorder_branch` | `run` | source_missing_or_unreadable, upstream_artifact_newer |

Forbidden uses: `broker_submit`, `runtime_threshold_apply`, `provider_route_change`, `bot_restart_trigger`, `sizing_formula_runtime_apply_without_guard`, `hard_safety_bypass`
