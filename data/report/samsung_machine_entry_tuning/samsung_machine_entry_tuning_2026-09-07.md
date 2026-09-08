# Samsung machine entry tuning — 2026-09-07

- Decision: actual-state audit; causal rise/rebound optimization belongs to machine entry timing. No subset-only promotion or same-day runtime change.
- Source: target-date machine state plus prior artifacts from this producer only; no market-history query.
- Clean baseline: 2026-06-05
- Clean-baseline actual observations: 19/65 trading dates; missing dates are coverage only and are not imputed.
- Decision windows use only the latest exact runtime-policy/target/quantity cohort; cross-version totals are audit-only.
- Outcome amendment ledger: pass / 21 records.
- Held/unresolved inventory in the latest exact cohort blocks candidate readiness; there is no stop-loss or forced exit.

## Daily

| Machine | Cohort | Source | Attempt | Status | Completed legs | Manual exits/losses | Held | Unresolved |
|---|---|---|---:|---|---:|---:|---:|---:|
| morning | two_leg_runtime | pass | 1 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| morning_reentry | source_unavailable | gap | 0 | UNKNOWN | 0 | 0/0 | 0 | 0 |
| midday | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |
| afternoon | two_leg_runtime | pass | 0 | NO_TRADE | 0 | 0/0 | 0 | 0 |

## Cumulative decision

- morning: `collect_sample`; complete episodes 7/8, clean-baseline cumulative equal-weight/weighted EV -1.31609/-1.403252; rolling10/20 0.4006/-1.403252; broker-priced legs 6/8; post-apply net/day KRW -215750.028/-14383.335; signal rate 0.466667; avg realized hold min 2117.867; estimated days to floor 5.
- morning_reentry: `source_quality_blocked`; complete episodes 1/8, clean-baseline cumulative equal-weight/weighted EV 0.357104/0.357103; rolling10/20 None/0.357103; broker-priced legs 2/8; post-apply net/day KRW 19229.998/1201.875; signal rate 0.0625; avg realized hold min 99.617; estimated days to floor 112.
- midday: `evidence_accumulating_low_signal_rate`; complete episodes 1/8, clean-baseline cumulative equal-weight/weighted EV None/None; rolling10/20 None/None; broker-priced legs 0/8; post-apply net/day KRW 0/0.0; signal rate 0.0625; avg realized hold min None; estimated days to floor None.
- afternoon: `evidence_accumulating_low_signal_rate`; complete episodes 2/8, clean-baseline cumulative equal-weight/weighted EV 0.387436/0.387084; rolling10/20 0.387084/0.387084; broker-priced legs 4/8; post-apply net/day KRW 39560.003/2472.5; signal rate 0.1875; avg realized hold min 40.95; estimated days to floor 48.

Signal subsets are diagnostic only. New confirmation candidates require the entry-timing causal replay and apply contracts. Only an actually applied legacy tightening can be unwound here using exact-epoch evidence.
