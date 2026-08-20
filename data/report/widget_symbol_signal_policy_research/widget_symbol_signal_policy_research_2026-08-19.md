# Widget symbol signal policy research — 2026-08-19

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_pass_widget_signal_policy_candidate | midday | 1 | 20/7 | 0.202994/0.015471 | -1.692537 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 12/4 | 0.148225/-0.315942 | -1.790909 |
| 080220 | 제주반도체 | holdout_pass_widget_signal_policy_candidate | morning | 1 | 20/8 | 0.107642/0.034234 | -1.009061 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 32/12 | 0.430259/-0.431112 | -2.596514 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
