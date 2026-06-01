# Tuning Performance Control Tower - 2026-05-26

## 판정

- 판정: `postclose_verifier_blocked`
- bridge_policy_emit_state: `-`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `fail`.
- 근거: LDM `sim_auto_approved=183` (`+64`), `live_auto_apply_ready=1` (`+0`), swing sim-auto `0` (`+0`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `1`, promotion_window `0`, bridge_ready `2`.
- Parent bucket: daily parent_granularity_status `0`/`None`, mtd `0`/`None`, absorbed_sample `0`, conflict_children `0`.
- Bridge/verifier: greenfield_policy_emit_state `-`, promotion_contract_passed `False`, verifier_status `fail`, verifier_missing `["lifecycle_bucket_discovery_mtd_missing", "lifecycle_bucket_discovery_rolling10d_missing", "lifecycle_bucket_discovery_rolling5d_missing", "lifecycle_decision_matrix_mtd_missing", "lifecycle_decision_matrix_rolling10d_missing", "lifecycle_decision_matrix_rolling5d_missing", "runtime_apply_bridge_child_combo_policy_authority", "runtime_apply_bridge_daily_only_live_authority"]`.
- Lifecycle bucket: candidates `414` (`+35`), surfaced `184` (`+64`), sim-auto `183` (`+64`), live-ready `1` (`+0`).
- Lifecycle matrix: rows `48618` (`+48615`), joined `47005` (`+47003`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `74` (`+73`), complete `0` (`+0`), runtime `0` (`+0`), workorders `20` (`+19`).
- Holding/exit buckets: holding `38` (`+33`), exit `71` (`+64`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0`.
- Lifecycle join contract: blocked `none`, incomplete `None`, top reason `None`.
- Swing matrix: rows `203216` (`+62917`), probe `201344` (`+62245`), pending future quotes `1211` (`+555`).
- Swing bucket: sim-auto `0` (`+0`), code-patch `1` (`+1`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `10`, avg `0.088`, win-rate `0.6`.
- Sim split sample `730`, avg `-0.4989`, win-rate `0.3493`.
- EV warnings: `trade_review_missing, performance_tuning_missing, lifecycle_bucket_discovery:ai_review_ambiguous_live_candidate_kept_for_post_apply, lifecycle_bucket_discovery:ai_review_ambiguous_live_candidate_kept_for_post_apply, lifecycle_bucket_windows:rolling5d_missing, lifecycle_bucket_windows:rolling10d_missing, lifecycle_bucket_windows:mtd_missing, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes`.

## Workorder

- selected orders `93`, selected decisions `{"attach_existing_family": 65, "implement_now": 28}`, routes `{"auto_patch_required": 2, "block_source_quality": 1, "existing_family": 65, "implement_now": 7, "instrumentation_order": 18}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `pass`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-05-26.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-05-26.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-05-26.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-05-26.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-05-26.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-05-26.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-05-26.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-05-26.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-05-26.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-05-26.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-05-26.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-05-26.json` exists=true json_valid=true
