# Samsung machine entry tuning — 2026-09-10

- Decision: actual-state audit; causal rise/rebound optimization belongs to machine entry timing. No subset-only promotion or same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 22/68 trading dates; missing dates are coverage only and are not imputed.
- Decision windows use only the latest exact runtime-policy/target/quantity cohort; cross-version totals are audit-only.
- Outcome amendment ledger: pass / 22 records.
- Held/unresolved inventory in the latest exact cohort blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0/0 | 0 | 0 |
| morning_reentry | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |

## Cumulative decision

- morning: `auto_bounded_candidate_ready`; complete episodes 10/8, clean-baseline cumulative equal-weight/weighted EV -0.645975/-0.678836; rolling10/20 0.379151/-0.678836; broker-priced legs 10/8; post-apply net/day KRW -177210.011/-9845.001; signal rate 0.555556; avg realized hold min 1319.387; estimated days to floor 0.
- morning_reentry: `evidence_accumulating_low_signal_rate`; complete episodes 2/8, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 None/0.357103; broker-priced legs 2/8; post-apply net/day KRW 19229.998/1012.105; signal rate 0.105263; avg realized hold min 99.617; estimated days to floor 57.
- midday: `evidence_accumulating_low_signal_rate`; complete episodes 1/8, clean-baseline cumulative equal-weight/weighted EV None/None; rolling10/20 None/None; broker-priced legs 0/8; post-apply net/day KRW 0/0.0; signal rate 0.052632; avg realized hold min None; estimated days to floor None.
- afternoon: `collect_sample`; complete episodes 3/8, clean-baseline cumulative equal-weight/weighted EV 0.37394/0.373066; rolling10/20 0.373066/0.373066; broker-priced legs 6/8; post-apply net/day KRW 58589.993/3083.684; signal rate 0.210526; avg realized hold min 26.471; estimated days to floor 32.

Signal subsets are diagnostic only. New confirmation candidates require the entry-timing causal replay and apply contracts. Only an actually applied legacy tightening can be unwound here using exact-epoch evidence.
