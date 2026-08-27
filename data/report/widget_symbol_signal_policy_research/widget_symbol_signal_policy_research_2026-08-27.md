# Widget symbol signal policy research — 2026-08-27

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 11/0 | 0.220633/None | None |
| 010140 | 삼성중공업 | no_robust_calibration_policy | morning | 1 | 28/- | 0.005652/- | - |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 36/13 | 0.095508/-0.067149 | -1.395803 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 34/7 | 0.09849/-0.798311 | -1.402529 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
