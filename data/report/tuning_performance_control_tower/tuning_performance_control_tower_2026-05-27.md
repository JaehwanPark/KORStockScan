# Tuning Performance Control Tower - 2026-05-27

## 판정

- 판정: `postclose_verifier_blocked`
- bridge_policy_emit_state: `-`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `fail`.
- 근거: LDM `sim_auto_approved=185` (`+2`), `live_auto_apply_ready=1` (`+0`), swing sim-auto `0` (`+0`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `1`, promotion_window `0`, bridge_ready `1`.
- Parent bucket: daily parent_granularity_status `0`/`None`, mtd `0`/`None`, absorbed_sample `0`, conflict_children `0`.
- Bridge/verifier: greenfield_policy_emit_state `-`, promotion_contract_passed `False`, verifier_status `fail`, verifier_missing `["lifecycle_bucket_discovery_mtd_missing", "lifecycle_bucket_discovery_rolling10d_missing", "lifecycle_bucket_discovery_rolling5d_missing", "lifecycle_decision_matrix_mtd_missing", "lifecycle_decision_matrix_rolling10d_missing", "lifecycle_decision_matrix_rolling5d_missing", "runtime_apply_bridge_daily_only_live_authority"]`.
- Lifecycle bucket: candidates `379` (`-35`), surfaced `186` (`+2`), sim-auto `185` (`+2`), live-ready `1` (`+0`).
- Lifecycle matrix: rows `41172` (`-7446`), joined `39464` (`-7541`), promote-ready `1` (`+1`).
- Lifecycle flow: buckets `82` (`+8`), complete `0` (`+0`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `30` (`-8`), exit `54` (`-17`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0`.
- Lifecycle join contract: blocked `none`, incomplete `None`, top reason `None`.
- Swing matrix: rows `135311` (`-67905`), probe `132857` (`-68487`), pending future quotes `1712` (`+501`).
- Swing bucket: sim-auto `0` (`+0`), code-patch `0` (`-1`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `2`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `13`, avg `-0.0231`, win-rate `0.5385`.
- Sim split sample `659`, avg `-0.7163`, win-rate `0.3536`.
- EV warnings: `trade_review_missing, performance_tuning_missing, lifecycle_bucket_windows:rolling5d_missing, lifecycle_bucket_windows:rolling10d_missing, lifecycle_bucket_windows:mtd_missing, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_ai_review_warning`.

## Workorder

- selected orders `90`, selected decisions `{"attach_existing_family": 71, "implement_now": 19}`, routes `{"auto_patch_required": 2, "existing_family": 71, "implement_now": 2, "instrumentation_order": 15}`.
- pattern lab AI review source orders `1`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-27.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-27.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-27.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-27.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-27.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-27.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-27.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-27.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-27.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-27.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-27.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-27.json` exists=true json_valid=true
