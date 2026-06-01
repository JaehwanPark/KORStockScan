# Tuning Performance Control Tower - 2026-05-18

## 판정

- 판정: `source_gap_review_required`
- bridge_policy_emit_state: `-`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `fail`.
- 근거: LDM `sim_auto_approved=0` (`n/a`), `live_auto_apply_ready=0` (`n/a`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `0`/`None`, mtd `0`/`None`, absorbed_sample `0`, conflict_children `0`.
- Bridge/verifier: greenfield_policy_emit_state `-`, promotion_contract_passed `False`, verifier_status `fail`, verifier_missing `["lifecycle_bucket_discovery_mtd_missing", "lifecycle_bucket_discovery_rolling10d_missing", "lifecycle_bucket_discovery_rolling5d_missing", "lifecycle_decision_matrix_mtd_missing", "lifecycle_decision_matrix_rolling10d_missing", "lifecycle_decision_matrix_rolling5d_missing"]`.
- Lifecycle bucket: candidates `None` (`n/a`), surfaced `None` (`n/a`), sim-auto `None` (`n/a`), live-ready `None` (`n/a`).
- Lifecycle matrix: rows `489` (`+418`), joined `434` (`+368`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `11` (`+7`), complete `0` (`+0`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `7` (`+0`), exit `8` (`+8`), workorders `5`/`0`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0`.
- Lifecycle join contract: blocked `none`, incomplete `None`, top reason `None`.
- Swing matrix: rows `806062` (`n/a`), probe `806062` (`n/a`), pending future quotes `0` (`n/a`).
- Swing bucket: sim-auto `0` (`n/a`), code-patch `0` (`n/a`).
- Scalp sim control tower: approved `false`, policies `0`, sources `[]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `0`, avg `None`, win-rate `None`.
- Sim split sample `5`, avg `-1.546`, win-rate `0.2`.
- EV warnings: `trade_review_missing, performance_tuning_missing, scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:missing_action_bucket, scalp_entry_adm:prompt_context_not_loaded, lifecycle_bucket_discovery_missing, lifecycle_bucket_discovery_missing, lifecycle_bucket_windows:rolling5d_missing, lifecycle_bucket_windows:rolling10d_missing, lifecycle_bucket_windows:mtd_missing, lifecycle_ai_context_missing, lifecycle_ai_context_attribution_missing, swing_strategy_discovery_ev_missing, swing_lifecycle_decision_matrix:swing_strategy_discovery_sim_missing, institutional_flow_context_missing, pattern_lab_ai_review_missing, time_window_regime_counterfactual_missing, producer_gap_discovery_missing, stage_hook_workorder_discovery_missing, stage_hook_runtime_scaffold_missing, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `48`, selected decisions `{"attach_existing_family": 39, "implement_now": 9}`, routes `{"existing_family": 39, "instrumentation_order": 9}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `missing`, propagation `warning`, producer gap `missing`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-18.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-18.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-18.json` exists=false json_valid=false
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-18.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-18.json` exists=false json_valid=false
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-18.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-18.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-18.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-18.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-18.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-18.json` exists=false json_valid=false
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-18.json` exists=false json_valid=false
