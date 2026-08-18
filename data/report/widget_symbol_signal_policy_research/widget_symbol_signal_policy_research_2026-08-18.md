# Widget symbol signal policy research — 2026-08-18

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_pass_widget_signal_policy_candidate | midday | 1 | 20/7 | 0.202994/0.015471 | -1.692537 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 26/12 | 0.057263/-0.431839 | -1.393317 |
| 080220 | 제주반도체 | holdout_failed_no_widget_runtime_promotion | morning | 2 | 27/14 | 0.080134/-0.119233 | -1.285645 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 31/12 | 0.415727/-0.430708 | -2.596514 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
