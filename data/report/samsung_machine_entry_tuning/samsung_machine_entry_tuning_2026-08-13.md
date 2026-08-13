# Samsung machine entry tuning — 2026-08-13

- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 3/49 trading dates; missing dates are coverage only and are not imputed.
- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | COMPLETE | 1 | 0 | 0 |
| morning_reentry | prerequisite_not_met | pass | 0 | BLOCKED | 0 | 0 | 0 |
| midday | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 1 | HELD | 1 | 1 | 1 |

## Cumulative decision

- morning: `collect_sample`; complete episodes 2/20, clean-baseline cumulative equal-weight/weighted EV 0.201317/0.046253.
- morning_reentry: `collect_sample`; complete episodes 0/20, clean-baseline cumulative equal-weight/weighted EV None/None.
- midday: `collect_sample`; complete episodes 2/20, clean-baseline cumulative equal-weight/weighted EV 0.179918/0.158996.
- afternoon: `inventory_or_order_unresolved`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.184468/0.079932.

Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.
