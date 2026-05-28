# Tuning Performance Control Tower - 2026-05-28

## 판정

- 판정: `sim_progress_no_live_bucket`
- 근거: LDM `sim_auto_approved=172` (`-13`), `live_auto_apply_ready=0` (`-1`), swing sim-auto `13` (`+5`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Lifecycle bucket: candidates `500` (`+121`), surfaced `277` (`+91`), sim-auto `172` (`-13`), live-ready `0` (`-1`).
- Lifecycle matrix: rows `24465` (`-16707`), joined `23742` (`-15722`), promote-ready `1` (`+0`).
- Lifecycle flow: buckets `97` (`+15`), complete `84` (`+84`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `34` (`+4`), exit `68` (`+14`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0066`.
- Lifecycle join contract: blocked `false`, incomplete `12694`, top reason `missing_submit`.
- Swing matrix: rows `2922` (`+147`), probe `68` (`-253`), pending future quotes `2566` (`+328`).
- Swing bucket: sim-auto `13` (`+5`), code-patch `0` (`-14`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `17`, avg `-0.1282`, win-rate `0.4118`.
- Sim split sample `657`, avg `-0.9021`, win-rate `0.3409`.
- EV warnings: `lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:contamination_quarantine_live_auto_blocked:3, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_ai_review_warning`.

## Workorder

- selected orders `113`, selected decisions `{"attach_existing_family": 95, "implement_now": 18}`, routes `{"auto_patch_required": 17, "existing_family": 95, "instrumentation_order": 1}`.
- pattern lab AI review source orders `1`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `warning`.

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
