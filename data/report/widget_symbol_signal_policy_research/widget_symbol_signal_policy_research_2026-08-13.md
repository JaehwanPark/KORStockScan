# Widget symbol signal policy research — 2026-08-13

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | midday | 2 | 30/9 | 0.121357/-0.420901 | -2.144895 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 26/10 | 0.069136/-0.316063 | -1.393317 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 4 | 52/21 | 0.060411/-0.010137 | -1.588889 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 29/12 | 0.362968/-0.013627 | -2.596514 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
