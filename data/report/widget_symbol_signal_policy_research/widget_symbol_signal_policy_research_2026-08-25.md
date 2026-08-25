# Widget symbol signal policy research — 2026-08-25

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 3 | 14/0 | 0.127898/None | None |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 3 | 44/14 | 0.060951/-0.4001 | -1.393317 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 2 | 11/2 | 0.172009/-0.2 | -0.45974 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 21/11 | 0.101955/-0.783528 | -3.55097 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
