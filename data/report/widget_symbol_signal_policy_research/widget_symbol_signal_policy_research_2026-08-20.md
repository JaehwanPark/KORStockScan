# Widget symbol signal policy research — 2026-08-20

Clean-baseline completed KRX 1-minute replay; source-only, no runtime/order authority.

| Symbol | Name | Decision | Segment | Daily cap | Episodes(cal/hold) | EV(cal/hold) | Worst holdout |
|---|---|---|---|---:|---:|---:|---:|
| 006800 | 미래에셋증권 | holdout_pass_widget_signal_policy_candidate | midday | 1 | 20/6 | 0.043516/0.02021 | -0.823053 |
| 010140 | 삼성중공업 | holdout_failed_no_widget_runtime_promotion | afternoon | 1 | 27/12 | 0.075883/-0.451062 | -1.393317 |
| 080220 | 제주반도체 | holdout_pass_widget_signal_policy_candidate | morning | 1 | 21/7 | 0.107611/0.024582 | -1.009061 |
| 475150 | SK이터닉스 | holdout_failed_no_widget_runtime_promotion | midday | 1 | 33/12 | 0.44232/-0.575205 | -2.596514 |

A row without holdout values is diagnostic-only and has no promotion authority.
Historical BBO, spread, signed tape, investor flow, and external market context were not imputed.
Live promotion requires a separate reviewed collector/contract/execution implementation.
