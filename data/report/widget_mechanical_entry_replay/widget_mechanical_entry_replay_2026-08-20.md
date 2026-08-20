# Widget mechanical Entry-AI replay — 2026-08-20

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 258 | 64 | 31 | 181 | 12.015504 | 14.622642 | -0.542683 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 15 | 13 | 2 | 7 | 13.333333 | 22.222222 | -0.422277 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 010130 | 4 | 0 | 1 | 1 | 1 | -0.213163 |
| 016360 | 4 | 0 | 1 | 0 | 2 | -0.07726 |
| 028260 | 2 | 0 | 1 | 0 | 1 | -0.726904 |
| 036540 | 6 | 0 | 1 | 0 | 6 | -1.040195 |
| 064400 | 11 | 0 | 1 | 0 | 8 | -0.656948 |
| 079650 | 5 | 0 | 1 | 0 | 4 | -1.017315 |
| 086520 | 6 | 0 | 3 | 0 | 3 | -0.521148 |
| 089890 | 4 | 0 | 1 | 0 | 4 | -0.601302 |
| 124500 | 27 | 0 | 1 | 3 | 24 | -0.528524 |
| 241710 | 1 | 0 | 1 | 0 | 0 | 0.0 |
| 247540 | 8 | 0 | 1 | 0 | 3 | -0.392546 |
| 299660 | 6 | 0 | 1 | 1 | 5 | -1.038374 |
| 950260 | 5 | 0 | 1 | 1 | 3 | -0.168903 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
