# Widget mechanical Entry-AI replay — 2026-08-10

- authority: `offline_widget_mechanical_replay_only`
- runtime_effect: `false`
- actual_order_submitted: `false`
- outcome: 10m tight entry path (`+0.3% / -0.7%`)

| Cohort | Samples | Stocks | Target first | Adverse first | Target-first rate | Target share among decisive | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AI BUY | 0 | 0 | 0 | 0 | None | None | None |
| AI WAIT/DROP | 330 | 96 | 69 | 218 | 20.909091 | 24.041812 | -0.447219 |
| Mechanical signal (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (price-comparable) | 0 | 0 | 0 | 0 | None | None | None |
| Mechanical candidate before spread gate (AI-ask proxy) | 12 | 10 | 2 | 6 | 16.666667 | 25.0 | -0.194065 |

## Stock-code cohorts

Only cohorts with a mechanical signal or a pre-spread candidate are shown; the JSON artifact retains every joined stock code.

| Stock code | Joined | Mechanical signals | Pre-spread candidates | Target first | Adverse first | Equal-weight 10m end |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 000250 | 9 | 0 | 1 | 2 | 4 | 1.159878 |
| 011790 | 7 | 0 | 1 | 1 | 2 | -0.148706 |
| 036710 | 6 | 0 | 1 | 1 | 5 | -0.869676 |
| 050890 | 12 | 0 | 2 | 1 | 5 | -0.320978 |
| 064760 | 4 | 0 | 1 | 0 | 4 | -0.977995 |
| 196170 | 8 | 0 | 2 | 0 | 8 | -0.571048 |
| 272210 | 3 | 0 | 1 | 0 | 2 | -0.177177 |
| 310210 | 6 | 0 | 1 | 1 | 3 | -0.048902 |
| 327260 | 9 | 0 | 1 | 2 | 7 | -0.079953 |
| 454910 | 8 | 0 | 2 | 1 | 7 | -0.269734 |

## Scope limits

Samsung-specific peer relative strength, investor/program flow, and Yahoo external risk were not fabricated for other symbols. Portable-core passes are therefore capped at `ENTRY_CAUTION`. The 10-second promotion filter and stateful recovery-episode filter are not replayed from event-spaced AI snapshots.

The pre-spread AI-ask proxy keeps the Entry-AI executable ask only as a conservative decision-point sensitivity check. It is not the widget recommended-range fill result; rows whose recommended range excludes that ask remain price-noncomparable.

This daily report is diagnostic counterfactual evidence only. It cannot replace Entry AI, approve live runtime changes, or submit orders.
