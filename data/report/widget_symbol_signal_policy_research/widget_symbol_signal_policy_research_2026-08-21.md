# Widget symbol signal policy research — 2026-08-21

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 2 | 10/3 | 0.106888/0.223953 | -1.030565 |
| 010140 | 삼성중공업 | no_robust_calibration_policy | afternoon | 1 | 26/- | 0.002349/- | - |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 29/15 | 0.127385/-0.007692 | -1.588889 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 26/13 | 0.113113/-0.228231 | -2.707837 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
