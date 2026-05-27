# Tuning Performance Control Tower - 2026-05-27

## 판정

- 판정: `live_bucket_ready`
- 근거: LDM `sim_auto_approved=185` (`+2`), `live_auto_apply_ready=1` (`+0`), swing sim-auto `8` (`+2`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Lifecycle bucket: candidates `379` (`-35`), surfaced `186` (`+2`), sim-auto `185` (`+2`), live-ready `1` (`+0`).
- Lifecycle matrix: rows `41172` (`-7609`), joined `39464` (`-7704`), promote-ready `1` (`+0`).
- Swing matrix: rows `2775` (`+1054`), probe `321` (`+200`), pending future quotes `2238` (`+804`).
- Swing bucket: sim-auto `8` (`+2`), code-patch `14` (`-5`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `2`.

## EV 해석

- Daily completed trades `5`, win-rate `40.0`, avg profit pct `-0.34`, realized PnL KRW `408`.
- Real split sample `13`, avg `-0.0231`, win-rate `0.5385`.
- Sim split sample `659`, avg `-0.7163`, win-rate `0.3536`.
- EV warnings: `swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes`.

## Workorder

- selected orders `56`, selected decisions `{"attach_existing_family": 56}`, routes `{"existing_family": 55, "performance_optimization_order": 1}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `pass`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-27.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-27.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-27.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-27.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-27.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-27.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-27.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-27.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-27.json` exists=true json_valid=true
