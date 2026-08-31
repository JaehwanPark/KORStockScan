# Samsung machine entry tuning — 2026-08-31

- Decision: actual-state observation plus a bounded next-PREOPEN candidate; no same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 14/60 trading dates; missing dates are coverage only and are not imputed.
- Held/unresolved inventory blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0/0 | 0 | 0 |
| morning_reentry | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |

## Cumulative decision

- morning: `inventory_or_order_unresolved`; complete episodes 5/20, clean-baseline cumulative equal-weight/weighted EV 0.250081/0.174756; rolling10/20 0.196387/0.174756; broker-priced legs 4/20.
- morning_reentry: `collect_sample`; complete episodes 1/20, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 None/0.357103; broker-priced legs 2/20.
- midday: `collect_sample`; complete episodes 3/20, clean-baseline cumulative equal-weight/weighted EV 0.179918/0.0; rolling10/20 0.0/0.0; broker-priced legs 0/20.
- afternoon: `inventory_or_order_unresolved`; complete episodes 2/20, clean-baseline cumulative equal-weight/weighted EV 0.313278/0.179876; rolling10/20 0.188696/0.179876; broker-priced legs 2/20.

Only source-quality-passed tightening subsets may enter the next-PREOPEN candidate. Relaxation, alternate cancel windows, and price-touch fill assumptions are not evaluated.
