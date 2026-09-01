# Widget symbol signal policy research — 2026-09-01

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 11/0 | 0.220633/None | None |
| 010140 | 삼성중공업 | no_robust_calibration_policy | morning | 1 | 31/- | 0.02839/- | - |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 2 | 72/24 | 0.084351/-0.030484 | -1.084956 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 28/5 | 0.253183/-0.396924 | -1.76322 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
