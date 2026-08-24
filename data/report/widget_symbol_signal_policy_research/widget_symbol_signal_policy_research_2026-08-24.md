# Widget symbol signal policy research — 2026-08-24

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 3 | 13/1 | 0.083126/0.820408 | 0.820408 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 27/13 | 0.076732/-0.451031 | -1.393317 |
| 080220 | 제주반도체 | holdout_pass_widget_signal_policy_candidate | afternoon | 1 | 30/14 | 0.094913/0.01982 | -1.11954 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 21/10 | 0.101955/-0.945997 | -3.55097 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
