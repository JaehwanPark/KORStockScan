# Samsung machine entry tuning — 2026-08-25

- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 10/56 trading dates; missing dates are coverage only and are not imputed.
- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|
| morning | source_unavailable | gap | 0 | UNKNOWN | 0 | 0 | 0 |
| morning_reentry | source_unavailable | gap | 0 | UNKNOWN | 0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0 | 0 |

## Cumulative decision

- morning: `source_quality_blocked`; complete episodes 4/20, clean-baseline cumulative equal-weight/weighted EV 0.187444/0.077269; rolling10/20 0.077269/0.077269; broker-priced legs 2/20.
- morning_reentry: `source_quality_blocked`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 0.357103/0.357103; broker-priced legs 2/20.
- midday: `collect_sample`; complete episodes 3/20, clean-baseline cumulative equal-weight/weighted EV 0.179918/0.0; rolling10/20 0.0/0.0; broker-priced legs 0/20.
- afternoon: `inventory_or_order_unresolved`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.193701/0.0; rolling10/20 0.0/0.0; broker-priced legs 0/20.

Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.
