# Widget mechanical Entry-AI replay — 2026-08-12

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 242 | 54 | 30 | 160 | 12.396694 | 15.789474 | -0.702201 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 11 | 8 | 1 | 8 | 9.090909 | 11.111111 | -0.715762 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 031980 | 19 | 0 | 3 | 2 | 12 | -0.64675 |
| 066570 | 8 | 0 | 3 | 0 | 8 | -1.110403 |
| 161890 | 19 | 0 | 1 | 7 | 8 | -0.372093 |
| 181710 | 9 | 0 | 1 | 1 | 8 | -1.246868 |
| 241710 | 7 | 0 | 1 | 2 | 5 | -0.492025 |
| 251970 | 4 | 0 | 1 | 0 | 4 | -0.772764 |
| 257720 | 26 | 0 | 2 | 4 | 13 | -0.345392 |
| 402340 | 12 | 0 | 2 | 0 | 0 | -0.344127 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
