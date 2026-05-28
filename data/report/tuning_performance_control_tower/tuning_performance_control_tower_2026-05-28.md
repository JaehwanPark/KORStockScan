# Tuning Performance Control Tower - 2026-05-28

## 판정

- 판정: `sim_progress_no_live_bucket`
- 근거: LDM `sim_auto_approved=176` (`-9`), `live_auto_apply_ready=0` (`-1`), swing sim-auto `16` (`+8`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Lifecycle bucket: candidates `385` (`+6`), surfaced `250` (`+64`), sim-auto `176` (`-9`), live-ready `0` (`-1`).
- Lifecycle matrix: rows `21807` (`-19365`), joined `21144` (`-18320`), promote-ready `1` (`+0`).
- Lifecycle flow: buckets `66` (`n/a`), complete `0` (`n/a`), runtime `0` (`n/a`), workorders `20` (`n/a`).
- Swing matrix: rows `2902` (`+127`), probe `48` (`-273`), pending future quotes `2483` (`+245`).
- Swing bucket: sim-auto `16` (`+8`), code-patch `32` (`+18`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `14`, avg `-0.3521`, win-rate `0.4286`.
- Sim split sample `657`, avg `-0.9021`, win-rate `0.3409`.
- EV warnings: `swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_currentness_audit_warning, pattern_lab_ai_review_warning, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `92`, selected decisions `{"attach_existing_family": 84, "implement_now": 8}`, routes `{"existing_family": 84, "implement_now": 8}`.
- pattern lab AI review source orders `4`, pattern lab currentness source orders `2`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `warning`, AI review `warning`, propagation `warning`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-28.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-28.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-28.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-28.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-28.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-28.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-28.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-28.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-28.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-28.json` exists=true json_valid=true
