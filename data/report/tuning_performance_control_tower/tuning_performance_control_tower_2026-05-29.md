# Tuning Performance Control Tower - 2026-05-29

## 판정

- 판정: `sim_progress_no_live_bucket`
- 근거: LDM `sim_auto_approved=123` (`-17`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`+0`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Lifecycle bucket: candidates `500` (`+0`), surfaced `238` (`-11`), sim-auto `123` (`-17`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `22977` (`-1507`), joined `22200` (`-1561`), promote-ready `1` (`+1`).
- Lifecycle flow: buckets `102` (`+5`), complete `81` (`-3`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `34` (`+0`), exit `70` (`+2`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.007`.
- Lifecycle join contract: blocked `false`, incomplete `11437`, top reason `missing_submit`.
- Swing matrix: rows `3717` (`+445`), probe `81` (`+13`), pending future quotes `2729` (`+112`).
- Swing bucket: sim-auto `0` (`+0`), code-patch `0` (`+0`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `3`, win-rate `33.33`, avg profit pct `-1.17`, realized PnL KRW `-6151`.
- Real split sample `21`, avg `-0.3848`, win-rate `0.381`.
- Sim split sample `726`, avg `-0.7804`, win-rate `0.3705`.
- EV warnings: `swing_lab_carryover:2, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_ai_review_warning`.

## Workorder

- selected orders `108`, selected decisions `{"attach_existing_family": 106, "implement_now": 2}`, routes `{"existing_family": 106, "implement_now": 2}`.
- pattern lab AI review source orders `2`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-29.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-29.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-29.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-29.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-29.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-29.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-29.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-29.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-29.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-29.json` exists=true json_valid=true
