# Widget mechanical Entry-AI replay — 2026-08-27

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 198 | 56 | 36 | 129 | 18.181818 | 21.818182 | -0.491203 |
| Mechanical signal (price-comparable) | 1 | 1 | 0 | 0 | 0.0 | None | -0.210084 |
| Mechanical candidate before spread gate (price-comparable) | 1 | 1 | 0 | 0 | 0.0 | None | -0.210084 |
| Mechanical candidate before spread gate (AI-ask proxy) | 12 | 10 | 1 | 9 | 8.333333 | 10.0 | -0.722066 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000500 | 12 | 0 | 4 | 2 | 9 | -0.428442 |
| 034220 | 1 | 0 | 1 | 0 | 1 | -0.307062 |
| 052690 | 3 | 0 | 1 | 0 | 1 | -0.258071 |
| 086520 | 4 | 0 | 1 | 1 | 3 | -0.302236 |
| 107640 | 13 | 0 | 1 | 2 | 11 | -0.558964 |
| 108860 | 1 | 1 | 1 | 0 | 0 | -0.210084 |
| 272210 | 3 | 0 | 1 | 0 | 0 | -0.216842 |
| 377300 | 6 | 0 | 1 | 0 | 4 | -0.485949 |
| 441270 | 8 | 0 | 1 | 4 | 4 | -0.199835 |
| 950260 | 9 | 0 | 1 | 1 | 8 | -0.084388 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
