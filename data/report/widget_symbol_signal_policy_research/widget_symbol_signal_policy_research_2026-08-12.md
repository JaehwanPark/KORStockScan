# Widget symbol signal policy research — 2026-08-12

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | midday | 38/13 | 0.038597/-0.2 | -2.144895 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | morning | 13/3 | 0.059924/-0.743901 | -1.790909 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 48/24 | 0.084483/-0.079163 | -1.588889 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 80/28 | 0.0137/-0.167403 | -2.624242 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
