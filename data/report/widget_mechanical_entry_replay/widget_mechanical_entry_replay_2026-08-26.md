# Widget mechanical Entry-AI replay — 2026-08-26

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 202 | 55 | 37 | 142 | 18.316832 | 20.670391 | -0.704113 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 13 | 9 | 0 | 8 | 0.0 | 0.0 | -0.468518 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000100 | 6 | 0 | 1 | 1 | 3 | -0.20013 |
| 000720 | 19 | 0 | 5 | 6 | 8 | -0.310381 |
| 014620 | 5 | 0 | 1 | 0 | 4 | -0.582104 |
| 023160 | 4 | 0 | 1 | 0 | 4 | -0.951743 |
| 079900 | 28 | 0 | 1 | 1 | 24 | -0.664033 |
| 082740 | 1 | 0 | 1 | 0 | 1 | -0.511247 |
| 096530 | 3 | 0 | 1 | 0 | 3 | -0.563866 |
| 103590 | 3 | 0 | 1 | 0 | 3 | -0.720743 |
| 375500 | 6 | 0 | 2 | 0 | 6 | -0.862441 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
