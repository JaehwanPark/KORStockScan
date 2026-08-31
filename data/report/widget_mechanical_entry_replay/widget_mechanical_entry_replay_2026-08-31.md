# Widget mechanical Entry-AI replay — 2026-08-31

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 204 | 49 | 42 | 123 | 20.588235 | 25.454545 | -0.439267 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 9 | 7 | 1 | 6 | 11.111111 | 14.285714 | -0.920591 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 023530 | 8 | 0 | 3 | 0 | 4 | -0.200594 |
| 066970 | 9 | 0 | 1 | 2 | 5 | -0.627969 |
| 067290 | 3 | 0 | 2 | 0 | 3 | -2.191235 |
| 161000 | 5 | 0 | 1 | 1 | 1 | -1.066483 |
| 214150 | 16 | 0 | 1 | 0 | 15 | -0.701254 |
| 356860 | 3 | 0 | 1 | 0 | 2 | -0.549393 |
| 476060 | 26 | 0 | 1 | 10 | 12 | -0.037022 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
