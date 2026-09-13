# Widget mechanical Entry-AI replay — 2026-09-11

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 179 | 68 | 34 | 120 | 18.994413 | 22.077922 | -0.809135 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 6 | 6 | 2 | 3 | 33.333333 | 40.0 | -0.482851 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 001820 | 13 | 0 | 1 | 0 | 13 | -1.049861 |
| 064550 | 5 | 0 | 1 | 0 | 4 | -0.975004 |
| 126730 | 2 | 0 | 1 | 1 | 0 | 3.373608 |
| 138930 | 1 | 0 | 1 | 0 | 0 | -0.618429 |
| 356890 | 3 | 0 | 2 | 0 | 2 | -3.187318 |
| 900270 | 2 | 0 | 1 | 1 | 1 | -2.018089 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
