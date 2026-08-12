# Widget symbol signal policy research — 2026-08-11

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|
| 006800 | 미래에셋증권 | no_robust_calibration_policy | midday | 38/- | 0.038597/- | - |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 40/10 | 0.067488/-0.293458 | -1.393317 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 45/22 | 0.114222/-0.344771 | -1.873102 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 77/31 | 0.034684/-0.194129 | -2.624242 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
