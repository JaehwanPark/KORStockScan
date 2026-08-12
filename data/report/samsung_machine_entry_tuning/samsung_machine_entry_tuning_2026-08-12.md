# Samsung machine entry tuning — 2026-08-12

- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 2/48 trading dates; missing dates are coverage only and are not imputed.
- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0 | 0 |
| morning_reentry | pre_effective_not_applicable | not_applicable | 0 | NOT_EFFECTIVE | 0 | 0 | 0 |
| midday | two_leg_runtime | pass | 1 | COMPLETE | 1 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 1 | COMPLETE | 1 | 0 | 0 |

## Cumulative decision

- morning: `collect_sample`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.213651/0.213651.
- morning_reentry: `not_effective`; complete episodes 0/20, clean-baseline cumulative equal-weight/weighted EV None/None.
- midday: `collect_sample`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.191389/0.095788.
- afternoon: `collect_sample`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.193701/0.096946.

Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.
