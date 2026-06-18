# Entry Cancel Wait Tuning 2026-06-18

- family: `entry_cancel_wait_runtime`
- source_quality_status: `pass`
- enabled: `true` (automatic OFF forbidden)
- excluded_consumers: `ADM, LDM, lifecycle_bucket, threshold_cycle_ev, runtime_apply_bridge`

| profile | previous | recommended | state | completed |
|---|---:|---:|---|---:|
| standard | 60 | 60 | hold_best_unchanged | 20 |
| breakout | 120 | 120 | hold_sample | 0 |
| pullback | 600 | 600 | hold_sample | 0 |
| reserve | 1200 | 1200 | hold_sample | 0 |
