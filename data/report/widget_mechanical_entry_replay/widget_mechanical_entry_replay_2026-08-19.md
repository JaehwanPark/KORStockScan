# Widget mechanical Entry-AI replay — 2026-08-19

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 160 | 58 | 32 | 113 | 20.0 | 22.068966 | -0.823649 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 11 | 10 | 2 | 6 | 18.181818 | 25.0 | -0.594418 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 006660 | 7 | 0 | 1 | 1 | 6 | -0.23629 |
| 009520 | 5 | 0 | 2 | 2 | 3 | 0.207413 |
| 036800 | 9 | 0 | 1 | 3 | 6 | -1.115567 |
| 082920 | 6 | 0 | 1 | 0 | 6 | -0.465781 |
| 095340 | 5 | 0 | 3 | 0 | 2 | -0.799612 |
| 095610 | 2 | 0 | 1 | 0 | 0 | -0.270797 |
| 101730 | 12 | 0 | 1 | 4 | 8 | -1.188412 |
| 323280 | 3 | 0 | 1 | 0 | 3 | -1.111569 |
| 336260 | 6 | 0 | 1 | 1 | 4 | -0.594635 |
| 468530 | 2 | 0 | 1 | 0 | 2 | 0.51007 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
