# Widget symbol signal policy research — 2026-08-28

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 11/0 | 0.220633/None | None |
| 010140 | 삼성중공업 | holdout_pass_widget_signal_policy_candidate | morning | 1 | 29/15 | 0.028479/0.136558 | -1.215222 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 37/13 | 0.101113/-0.069887 | -1.395803 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 26/7 | 0.235991/-0.161551 | -1.76322 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
