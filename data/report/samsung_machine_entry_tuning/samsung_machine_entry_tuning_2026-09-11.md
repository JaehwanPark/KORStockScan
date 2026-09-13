# Samsung machine entry tuning — 2026-09-11

- Decision: actual-state audit; causal rise/rebound optimization belongs to machine entry timing. No subset-only promotion or same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 23/69 trading dates; missing dates are coverage only and are not imputed.
- Decision windows use only the latest exact runtime-policy/target/quantity cohort; cross-version totals are audit-only.
- Outcome amendment ledger: pass / 23 records.
- Held/unresolved inventory in the latest exact cohort blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|---:|
| morning | two_leg_runtime | gap | 1 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| morning_reentry | source_unavailable | gap | 0 | UNKNOWN | 0 | 0/0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |

## Cumulative decision

- morning: `source_quality_blocked`; complete episodes 10/8, clean-baseline cumulative equal-weight/weighted EV -0.645975/-0.678836; rolling10/20 0.379151/-0.678836; broker-priced legs 10/8; post-apply net/day KRW -177210.011/-9326.843; signal rate 0.526316; avg realized hold min 1319.387; estimated days to floor 0.
- morning_reentry: `source_quality_blocked`; complete episodes 2/8, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 None/0.357103; broker-priced legs 2/8; post-apply net/day KRW 19229.998/961.5; signal rate 0.1; avg realized hold min 99.617; estimated days to floor 60.
- midday: `evidence_accumulating_low_signal_rate`; complete episodes 1/8, clean-baseline cumulative equal-weight/weighted EV None/None; rolling10/20 None/None; broker-priced legs 0/8; post-apply net/day KRW 0/0.0; signal rate 0.05; avg realized hold min None; estimated days to floor None.
- afternoon: `collect_sample`; complete episodes 3/8, clean-baseline cumulative equal-weight/weighted EV 0.37394/0.373066; rolling10/20 0.373066/0.373066; broker-priced legs 6/8; post-apply net/day KRW 58589.993/2929.5; signal rate 0.2; avg realized hold min 26.471; estimated days to floor 34.

Signal subsets are diagnostic only. New confirmation candidates require the entry-timing causal replay and apply contracts. Only an actually applied legacy tightening can be unwound here using exact-epoch evidence.
