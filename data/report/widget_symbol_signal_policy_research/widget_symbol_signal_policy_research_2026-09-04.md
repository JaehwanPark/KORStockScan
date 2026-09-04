# Widget symbol signal policy research — 2026-09-04

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_failed_no_widget_runtime_promotion | afternoon | 3 | 14/1 | 0.119092/-0.841621 | -0.841621 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | morning | 1 | 34/14 | 0.104395/-0.25113 | -1.423317 |
| 080220 | 제주반도체 | holdout_pass_widget_signal_policy_candidate | morning | 1 | 22/8 | 0.295484/0.043879 | -1.63647 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 29/5 | 0.278716/-0.688506 | -1.76322 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
