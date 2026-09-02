# Widget symbol signal policy research — 2026-09-02

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 11/0 | 0.220633/None | None |
| 010140 | 삼성중공업 | no_robust_calibration_policy | morning | 1 | 32/- | 0.055188/- | - |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | morning | 3 | 26/8 | 0.128243/-0.498903 | -3.325 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 29/4 | 0.278716/-0.701647 | -1.76322 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
