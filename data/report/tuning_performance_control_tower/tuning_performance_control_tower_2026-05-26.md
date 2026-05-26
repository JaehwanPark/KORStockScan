# Tuning Performance Control Tower - 2026-05-26

## 판정

- 판정: `sim_progress_no_live_bucket`
- 근거: LDM `sim_auto_approved=184` (`+65`), `live_auto_apply_ready=0` (`-1`), swing sim-auto `6` (`+2`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Lifecycle bucket: candidates `414` (`+35`), surfaced `184` (`+64`), sim-auto `184` (`+65`), live-ready `0` (`-1`).
- Lifecycle matrix: rows `48781` (`+13553`), joined `47168` (`+13537`), promote-ready `1` (`+0`).
- Swing matrix: rows `1721` (`+521`), probe `121` (`+121`), pending future quotes `1434` (`+316`).
- Swing bucket: sim-auto `6` (`+2`), code-patch `19` (`+15`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `7`, win-rate `57.14`, avg profit pct `-0.46`, realized PnL KRW `-2184`.
- Real split sample `10`, avg `0.088`, win-rate `0.6`.
- Sim split sample `730`, avg `-0.4989`, win-rate `0.3493`.
- EV warnings: `swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes`.

## Workorder

- selected orders `64`, selected decisions `{"attach_existing_family": 26, "implement_now": 38}`, routes `{"block_source_quality": 1, "existing_family": 26, "implement_now": 7, "instrumentation_order": 30}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `pass`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-26.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-26.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-26.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-26.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-26.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-26.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-26.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-26.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-26.json` exists=true json_valid=true
