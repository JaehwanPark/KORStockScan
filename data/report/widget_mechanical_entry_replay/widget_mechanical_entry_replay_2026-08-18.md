# Widget mechanical Entry-AI replay — 2026-08-18

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 266 | 61 | 62 | 175 | 23.308271 | 26.160338 | -0.635671 |
| Mechanical signal (price-comparable) | 1 | 1 | 0 | 1 | 0.0 | 0.0 | -0.88968 |
| Mechanical candidate before spread gate (price-comparable) | 1 | 1 | 0 | 1 | 0.0 | 0.0 | -0.88968 |
| Mechanical candidate before spread gate (AI-ask proxy) | 12 | 9 | 0 | 10 | 0.0 | 0.0 | -0.725556 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 009900 | 3 | 0 | 1 | 0 | 3 | -0.893303 |
| 025980 | 8 | 0 | 1 | 1 | 6 | -0.074316 |
| 036200 | 6 | 0 | 1 | 0 | 5 | -0.99391 |
| 036930 | 11 | 0 | 2 | 1 | 8 | -0.70425 |
| 067310 | 5 | 0 | 1 | 2 | 3 | -0.681634 |
| 096770 | 14 | 0 | 3 | 1 | 10 | -0.635667 |
| 365660 | 2 | 1 | 1 | 0 | 1 | -0.776515 |
| 475560 | 23 | 0 | 1 | 5 | 12 | -1.005421 |
| 489790 | 11 | 0 | 1 | 1 | 10 | -0.418624 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
