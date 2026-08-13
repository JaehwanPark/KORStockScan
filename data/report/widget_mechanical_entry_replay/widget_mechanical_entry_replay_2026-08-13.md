# Widget mechanical Entry-AI replay — 2026-08-13

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 201 | 48 | 30 | 136 | 14.925373 | 18.072289 | -0.619235 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 13 | 9 | 0 | 9 | 0.0 | 0.0 | -0.920407 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 009150 | 15 | 0 | 1 | 5 | 2 | -0.125663 |
| 025560 | 2 | 0 | 1 | 1 | 1 | -0.202845 |
| 084370 | 2 | 0 | 1 | 0 | 2 | -0.826787 |
| 090460 | 3 | 0 | 1 | 0 | 2 | -0.654243 |
| 090710 | 13 | 0 | 4 | 0 | 10 | -0.806072 |
| 103590 | 8 | 0 | 2 | 1 | 5 | -0.623935 |
| 119850 | 20 | 0 | 3 | 3 | 17 | -0.313419 |
| 153890 | 5 | 0 | 1 | 1 | 4 | -1.96072 |
| 425420 | 5 | 0 | 1 | 1 | 4 | -0.899125 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
