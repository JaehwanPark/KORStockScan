# Widget symbol signal policy research — 2026-09-10

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 26/0 | 0.119215/None | None |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 38/14 | 0.041521/-0.212841 | -1.423317 |
| 080220 | 제주반도체 | component_economics_or_holdout_not_ready | morning | 1 | 23/10 | 0.316576/-0.025918 | -1.63647 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 33/3 | 0.135926/0.401712 | -0.628406 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
