# Widget mechanical Entry-AI replay — 2026-08-05

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 379 | 109 | 59 | 281 | 15.567282 | 17.352941 | -0.676727 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 17 | 15 | 2 | 11 | 11.764706 | 15.384615 | -0.616402 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 009830 | 10 | 0 | 1 | 2 | 7 | -0.800549 |
| 010120 | 4 | 0 | 2 | 0 | 4 | -1.404331 |
| 011070 | 17 | 0 | 1 | 1 | 13 | -0.573674 |
| 034020 | 1 | 0 | 1 | 0 | 1 | -0.918635 |
| 042660 | 21 | 0 | 3 | 0 | 7 | -0.421907 |
| 066570 | 5 | 0 | 1 | 0 | 4 | -0.292116 |
| 067290 | 7 | 0 | 1 | 0 | 6 | -0.896365 |
| 080580 | 3 | 0 | 1 | 2 | 1 | -0.025815 |
| 103140 | 8 | 0 | 1 | 0 | 7 | -0.503872 |
| 112610 | 8 | 0 | 1 | 0 | 7 | -0.589302 |
| 122350 | 14 | 0 | 1 | 3 | 9 | -1.005341 |
| 217590 | 5 | 0 | 1 | 1 | 4 | -0.169928 |
| 278470 | 12 | 0 | 1 | 0 | 12 | -0.666047 |
| 450080 | 14 | 0 | 1 | 1 | 13 | -0.652672 |
| 475150 | 7 | 0 | 1 | 0 | 7 | -0.534133 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
