# Automation Chain Trigger Decision 2026-08-14

- scope: `all`
- run_count: `9`
- skip_count: `0`
- disabled_count: `5`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Decisions

| step | decision | reasons |
| --- | --- | --- |
| `lifecycle_window_rolling5d` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `lifecycle_window_rolling10d` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `lifecycle_window_mtd` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `pattern_lab_currentness_audit` | `run` | upstream_drift_signal |
| `pattern_lab_ai_review` | `run` | upstream_drift_signal |
| `observation_source_quality_audit` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `observation_source_quality_backfill_audit` | `disabled_success` | disabled_by_runtime_policy |
| `codebase_performance_workorder` | `disabled_success` | disabled_by_runtime_policy |
| `producer_gap_discovery` | `disabled_success` | disabled_by_runtime_policy |
| `stage_hook_workorder_discovery` | `disabled_success` | disabled_by_runtime_policy |
| `stage_hook_runtime_scaffold` | `disabled_success` | disabled_by_runtime_policy |
| `pattern_lab_propagation_audit` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `runtime_apply_gap_audit` | `run` | upstream_drift_signal |
| `workorder_branch` | `run` | source_missing_or_unreadable, upstream_artifact_newer |

Forbidden uses: `broker_submit`, `runtime_threshold_apply`, `provider_route_change`, `bot_restart_trigger`, `sizing_formula_runtime_apply_without_guard`, `hard_safety_bypass`
