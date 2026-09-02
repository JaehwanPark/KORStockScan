# Widget mechanical Entry-AI replay — 2026-09-02

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 169 | 44 | 41 | 113 | 24.260355 | 26.623377 | -0.451572 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 6 | 6 | 3 | 3 | 50.0 | 50.0 | -0.154009 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 024060 | 11 | 0 | 1 | 5 | 6 | -0.661677 |
| 044490 | 5 | 0 | 2 | 0 | 4 | -1.095017 |
| 092870 | 3 | 0 | 1 | 1 | 2 | -0.648756 |
| 232140 | 10 | 0 | 1 | 2 | 7 | -0.371451 |
| 249420 | 20 | 0 | 1 | 9 | 9 | 0.168854 |
| 396300 | 5 | 0 | 2 | 1 | 4 | -0.062633 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
