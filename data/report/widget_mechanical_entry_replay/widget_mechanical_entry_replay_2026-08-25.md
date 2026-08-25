# Widget mechanical Entry-AI replay — 2026-08-25

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 189 | 48 | 26 | 126 | 13.756614 | 17.105263 | -0.552253 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 5 | 4 | 1 | 4 | 20.0 | 20.0 | -0.708259 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 052690 | 15 | 0 | 1 | 4 | 11 | -0.866769 |
| 138040 | 8 | 0 | 1 | 0 | 2 | -0.446998 |
| 257720 | 11 | 0 | 2 | 0 | 11 | -0.703635 |
| 388050 | 9 | 0 | 1 | 0 | 8 | -0.976496 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
