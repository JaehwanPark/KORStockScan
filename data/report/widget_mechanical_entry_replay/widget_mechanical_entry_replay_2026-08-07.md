# Widget mechanical Entry-AI replay — 2026-08-07

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 285 | 82 | 46 | 201 | 16.140351 | 18.623482 | -0.720482 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 12 | 10 | 1 | 9 | 8.333333 | 10.0 | -0.183752 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 003670 | 15 | 0 | 1 | 8 | 5 | -0.128625 |
| 006400 | 14 | 0 | 2 | 1 | 7 | -0.260002 |
| 017900 | 3 | 0 | 1 | 0 | 3 | -1.533973 |
| 028670 | 5 | 0 | 1 | 0 | 5 | -0.892375 |
| 035720 | 15 | 0 | 2 | 2 | 13 | -0.452685 |
| 066970 | 8 | 0 | 1 | 1 | 5 | -1.146457 |
| 069540 | 8 | 0 | 1 | 0 | 8 | -1.400211 |
| 282330 | 11 | 0 | 2 | 0 | 8 | -0.401002 |
| 419050 | 5 | 0 | 1 | 1 | 2 | 0.717726 |
| 475040 | 5 | 0 | 1 | 0 | 5 | -1.522413 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
