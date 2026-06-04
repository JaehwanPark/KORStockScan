# Automation Chain Trigger Decision 2026-06-04

- scope: `all`
- run_count: `15`
- skip_count: `0`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Decisions

| step | decision | reasons |
| --- | --- | --- |
| `lifecycle_window_rolling5d` | `run` | upstream_drift_signal |
| `lifecycle_window_rolling10d` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `lifecycle_window_mtd` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `scalp_sim_ai_deferred_review` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `pattern_lab_currentness_audit` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `pattern_lab_ai_review` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `observation_source_quality_audit` | `run` | upstream_artifact_newer, upstream_drift_signal |
| `observation_source_quality_backfill_audit` | `run` | output_missing_or_unreadable, upstream_drift_signal |
| `codebase_performance_workorder` | `run` | output_missing_or_unreadable |
| `producer_gap_discovery` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `stage_hook_workorder_discovery` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `stage_hook_runtime_scaffold` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `pattern_lab_propagation_audit` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `runtime_apply_gap_audit` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |
| `workorder_branch` | `run` | output_missing_or_unreadable, source_missing_or_unreadable |

Forbidden uses: `broker_submit`, `runtime_threshold_apply`, `provider_route_change`, `bot_restart_trigger`, `position_cap_release`, `hard_safety_bypass`
