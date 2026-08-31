# Widget symbol signal policy research — 2026-08-31

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 11/0 | 0.220633/None | None |
| 010140 | 삼성중공업 | no_robust_calibration_policy | midday | 1 | 37/- | 0.02792/- | - |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | afternoon | 2 | 72/23 | 0.084351/-0.016576 | -1.084956 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 27/6 | 0.255252/-0.306439 | -1.76322 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
