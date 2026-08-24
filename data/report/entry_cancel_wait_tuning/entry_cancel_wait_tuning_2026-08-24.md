# Entry Cancel Wait Tuning 2026-08-24

- family: `entry_cancel_wait_runtime`
- source_quality_status: `pass`
- evidence_state: `observed_hold`
- registered_count: `3`
- completed_candidate_count: `9`
- threshold_change_supported: `False`
- enabled: `true` (automatic OFF forbidden)
- excluded_consumers: `ADM, LDM, lifecycle_bucket, threshold_cycle_ev, runtime_apply_bridge`

| profile | previous | recommended | state | completed |
|---|---:|---:|---|---:|
| standard | 90 | 90 | hold_sample | 9 |
| breakout | 120 | 120 | hold_sample | 0 |
| pullback | 600 | 600 | hold_sample | 0 |
| reserve | 1200 | 1200 | hold_sample | 0 |
