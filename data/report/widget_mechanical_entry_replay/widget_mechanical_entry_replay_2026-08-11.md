# Widget mechanical Entry-AI replay — 2026-08-11

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 191 | 44 | 34 | 123 | 17.801047 | 21.656051 | -0.485749 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 8 | 7 | 2 | 5 | 25.0 | 28.571429 | -0.236189 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 059120 | 4 | 0 | 1 | 1 | 3 | 0.416859 |
| 103590 | 5 | 0 | 2 | 0 | 5 | -0.686183 |
| 153890 | 4 | 0 | 2 | 0 | 4 | 1.419781 |
| 189330 | 9 | 0 | 1 | 4 | 5 | -0.216757 |
| 251970 | 8 | 0 | 1 | 0 | 8 | -1.03432 |
| 377300 | 12 | 0 | 2 | 2 | 7 | -0.481806 |
| 439090 | 10 | 0 | 1 | 2 | 5 | -0.29277 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
