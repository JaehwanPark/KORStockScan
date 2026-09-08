# Samsung machine entry tuning — 2026-09-08

- Decision: actual-state audit; causal rise/rebound optimization belongs to machine entry timing. No subset-only promotion or same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 20/66 trading dates; missing dates are coverage only and are not imputed.
- Decision windows use only the latest exact runtime-policy/target/quantity cohort; cross-version totals are audit-only.
- Outcome amendment ledger: pass / 21 records.
- Held/unresolved inventory in the latest exact cohort blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0/0 | 0 | 0 |
| morning_reentry | two_leg_runtime | pass | 1 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 1 | COMPLETE | 2 | 0/0 | 0 | 0 |

## Cumulative decision

- morning: `auto_bounded_candidate_ready`; complete episodes 8/8, clean-baseline cumulative equal-weight/weighted EV -0.89805/-0.946269; rolling10/20 0.384985/-0.946269; broker-priced legs 8/8; post-apply net/day KRW -196540.024/-12283.751; signal rate 0.5; avg realized hold min 1590.885; estimated days to floor 0.
- morning_reentry: `evidence_accumulating_low_signal_rate`; complete episodes 2/8, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 None/0.357103; broker-priced legs 2/8; post-apply net/day KRW 19229.998/1131.176; signal rate 0.117647; avg realized hold min 99.617; estimated days to floor 51.
- midday: `evidence_accumulating_low_signal_rate`; complete episodes 1/8, clean-baseline cumulative equal-weight/weighted EV None/None; rolling10/20 None/None; broker-priced legs 0/8; post-apply net/day KRW 0/0.0; signal rate 0.058824; avg realized hold min None; estimated days to floor None.
- afternoon: `collect_sample`; complete episodes 3/8, clean-baseline cumulative equal-weight/weighted EV 0.37394/0.373066; rolling10/20 0.373066/0.373066; broker-priced legs 6/8; post-apply net/day KRW 58589.993/3446.47; signal rate 0.235294; avg realized hold min 26.471; estimated days to floor 29.

Signal subsets are diagnostic only. New confirmation candidates require the entry-timing causal replay and apply contracts. Only an actually applied legacy tightening can be unwound here using exact-epoch evidence.
