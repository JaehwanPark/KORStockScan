# Samsung machine entry tuning — 2026-08-11

- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|
| morning | source_unavailable | gap | 0 | UNKNOWN | 0 | 0 | 0 |
| midday | legacy_one_leg_archive_only | gap | 0 | NO_TRADE | 0 | 0 | 0 |
| afternoon | legacy_one_leg_archive_only | gap | 1 | NO_TRADE | 0 | 0 | 0 |

## Cumulative decision

- morning: `source_quality_blocked`; complete episodes 0/20, rolling10/20/cumulative EV None/None/None.
- midday: `source_quality_blocked`; complete episodes 0/20, rolling10/20/cumulative EV None/None/None.
- afternoon: `source_quality_blocked`; complete episodes 0/20, rolling10/20/cumulative EV None/None/None.

Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.
