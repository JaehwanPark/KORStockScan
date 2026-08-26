# Widget symbol signal policy research — 2026-08-26

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 3 | 14/0 | 0.127898/None | None |
| 010140 | 삼성중공업 | no_robust_calibration_policy | afternoon | 2 | 42/- | 0.022102/- | - |
| 080220 | 제주반도체 | holdout_pass_widget_signal_policy_candidate | morning | 1 | 35/13 | 0.089082/0.080056 | -1.395219 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 33/8 | 0.071756/-0.580104 | -1.372529 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
