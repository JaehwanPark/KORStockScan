# Tuning Performance Control Tower - 2026-05-20

## 판정

- 판정: `source_gap_review_required`
- bridge_policy_emit_state: `-`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `fail`.
- 근거: LDM `sim_auto_approved=0` (`n/a`), `live_auto_apply_ready=0` (`n/a`), swing sim-auto `0` (`+0`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `0`/`None`, mtd `0`/`None`, absorbed_sample `0`, conflict_children `0`.
- Bridge/verifier: greenfield_policy_emit_state `-`, promotion_contract_passed `False`, verifier_status `fail`, verifier_missing `["lifecycle_bucket_discovery_mtd_missing", "lifecycle_bucket_discovery_rolling10d_missing", "lifecycle_bucket_discovery_rolling5d_missing", "lifecycle_decision_matrix_mtd_missing", "lifecycle_decision_matrix_rolling10d_missing", "lifecycle_decision_matrix_rolling5d_missing"]`.
- Lifecycle bucket: candidates `None` (`n/a`), surfaced `None` (`n/a`), sim-auto `None` (`n/a`), live-ready `None` (`n/a`).
- Lifecycle matrix: rows `16634` (`+2748`), joined `13910` (`+517`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `64` (`+29`), complete `0` (`+0`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `19` (`-9`), exit `60` (`+19`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0`.
- Lifecycle join contract: blocked `none`, incomplete `None`, top reason `None`.
- Swing matrix: rows `369365` (`+75211`), probe `368965` (`+74811`), pending future quotes `156` (`+156`).
- Swing bucket: sim-auto `0` (`+0`), code-patch `0` (`+0`).
- Scalp sim control tower: approved `false`, policies `0`, sources `[]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `0`, avg `None`, win-rate `None`.
- Sim split sample `343`, avg `-0.4434`, win-rate `0.3324`.
- EV warnings: `trade_review_missing, performance_tuning_missing, lifecycle_bucket_discovery_missing, lifecycle_bucket_discovery_missing, lifecycle_bucket_windows:rolling5d_missing, lifecycle_bucket_windows:rolling10d_missing, lifecycle_bucket_windows:mtd_missing, lifecycle_ai_context_attribution:lifecycle_ai_context_runtime_provenance_missing, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:sample_floor_not_met, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_ai_review_missing, time_window_regime_counterfactual_missing, producer_gap_discovery_missing, stage_hook_workorder_discovery_missing, stage_hook_runtime_scaffold_missing`.

## Workorder

- selected orders `63`, selected decisions `{"attach_existing_family": 47, "implement_now": 16}`, routes `{"existing_family": 47, "instrumentation_order": 16}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `missing`, propagation `pass`, producer gap `missing`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-20.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-20.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-20.json` exists=false json_valid=false
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-20.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-20.json` exists=false json_valid=false
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-20.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-20.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-20.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-20.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-20.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-20.json` exists=false json_valid=false
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-20.json` exists=false json_valid=false
