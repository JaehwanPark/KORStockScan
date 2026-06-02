# Tuning Performance Control Tower - 2026-06-02

## 판정

- 판정: `sim_progress_no_live_bucket`
- bridge_policy_emit_state: `not_emitted_no_complete_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_auto_approved=73` (`-22`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `7` (`+7`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `31`/`target_pass`, mtd `32`/`target_pass`, absorbed_sample `42881`, conflict_children `7`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_complete_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["active_sim_priority_preopen_handoff_pending"]`.
- Runtime gap audit: status `pass`, directives `1`, source_dimension_gap `150`, quiet_gap `308`, quiet_gap_directives `1`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `500` (`+0`), surfaced `218` (`-11`), sim-auto `73` (`-22`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `22915` (`-308`), joined `21855` (`-273`), promote-ready `1` (`+0`).
- Lifecycle flow: buckets `132` (`+12`), complete `113` (`+5`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `40` (`+4`), exit `64` (`+5`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0053`.
- Lifecycle join contract: blocked `false`, incomplete `21193`, top reason `missing_submit`.
- Swing matrix: rows `83272` (`-13366`), probe `77883` (`-13600`), pending future quotes `3634` (`+422`).
- Swing bucket: sim-auto `7` (`+7`), code-patch `0` (`+0`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `17`, win-rate `64.71`, avg profit pct `-0.13`, realized PnL KRW `15688`.
- Real split sample `43`, avg `-0.3223`, win-rate `0.4884`.
- Sim split sample `1229`, avg `-1.0201`, win-rate `0.3149`.
- EV warnings: `lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `102`, selected decisions `{"attach_existing_family": 102}`, routes `{"ai_review_coverage_review": 1, "existing_family": 98, "parent_conflict_exclusion_review": 1, "positive_source_only_review": 1, "source_dimension_rollup": 1}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `pass`, propagation `warning`, producer gap `pass`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-02.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-02.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-02.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-02.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-02.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-02.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-02.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-02.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-02.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-02.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-02.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-06-02.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-02.json` exists=true json_valid=true
