# Widget mechanical Entry-AI replay — 2026-08-06

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 443 | 114 | 73 | 302 | 16.478555 | 19.466667 | -0.588159 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 14 | 12 | 1 | 10 | 7.142857 | 9.090909 | -0.44747 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 006360 | 11 | 0 | 1 | 0 | 11 | -0.330254 |
| 032640 | 2 | 0 | 2 | 0 | 0 | -0.329598 |
| 073240 | 10 | 0 | 1 | 1 | 8 | -0.378073 |
| 089860 | 1 | 0 | 1 | 0 | 0 | -0.497512 |
| 090430 | 25 | 0 | 1 | 3 | 2 | -0.175656 |
| 144960 | 14 | 0 | 2 | 4 | 10 | -0.420472 |
| 153890 | 5 | 0 | 1 | 3 | 2 | 0.66286 |
| 278470 | 4 | 0 | 2 | 1 | 3 | -1.263647 |
| 317400 | 5 | 0 | 1 | 0 | 5 | -0.882154 |
| 347850 | 11 | 0 | 1 | 0 | 10 | -1.310741 |
| 387690 | 3 | 0 | 1 | 1 | 2 | -2.012337 |
| 476060 | 44 | 0 | 3 | 13 | 22 | -0.368984 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
