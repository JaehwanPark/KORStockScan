# Automation Chain Trigger Decision 2026-06-02

- scope: `all`
- run_count: `13`
- skip_count: `1`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Decisions

| step | decision | reasons |
| --- | --- | --- |
| `lifecycle_window_rolling5d` | `run` | upstream_drift_signal |
| `lifecycle_window_rolling10d` | `run` | upstream_drift_signal |
| `lifecycle_window_mtd` | `run` | upstream_drift_signal |
| `scalp_sim_ai_deferred_review` | `run` | upstream_drift_signal |
| `pattern_lab_currentness_audit` | `run` | upstream_drift_signal |
| `pattern_lab_ai_review` | `run` | upstream_drift_signal |
| `observation_source_quality_audit` | `run` | upstream_drift_signal |
| `codebase_performance_workorder` | `skip` | fresh_outputs_no_trigger |
| `producer_gap_discovery` | `run` | upstream_drift_signal |
| `stage_hook_workorder_discovery` | `run` | upstream_drift_signal |
| `stage_hook_runtime_scaffold` | `run` | upstream_drift_signal |
| `pattern_lab_propagation_audit` | `run` | upstream_drift_signal |
| `runtime_apply_gap_audit` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `workorder_branch` | `run` | upstream_artifact_newer, upstream_drift_signal |

Forbidden uses: `broker_submit`, `runtime_threshold_apply`, `provider_route_change`, `bot_restart_trigger`, `position_cap_release`, `hard_safety_bypass`
