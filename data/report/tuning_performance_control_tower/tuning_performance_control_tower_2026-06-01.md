# Tuning Performance Control Tower - 2026-06-01

## 판정

- 판정: `postclose_verifier_blocked`
- bridge_policy_emit_state: `not_emitted_no_complete_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_auto_approved=95` (`-28`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`-8`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `46`/`target_pass`, mtd `46`/`target_pass`, absorbed_sample `21575`, conflict_children `8`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_complete_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `fail`, verifier_missing `[]`.
- Lifecycle bucket: candidates `500` (`+0`), surfaced `229` (`-9`), sim-auto `95` (`-28`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `23223` (`+246`), joined `22128` (`-72`), promote-ready `1` (`+0`).
- Lifecycle flow: buckets `120` (`+18`), complete `108` (`+27`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `36` (`+2`), exit `59` (`-11`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.005`.
- Lifecycle join contract: blocked `false`, incomplete `21467`, top reason `missing_submit`.
- Swing matrix: rows `95903` (`+32065`), probe `91483` (`+31731`), pending future quotes `3256` (`+527`).
- Swing bucket: sim-auto `0` (`-8`), code-patch `0` (`+0`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `12`, win-rate `50.0`, avg profit pct `-0.56`, realized PnL KRW `-28652`.
- Real split sample `33`, avg `-0.4497`, win-rate `0.4242`.
- Sim split sample `1074`, avg `-0.8811`, win-rate `0.3417`.
- EV warnings: `lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery:pending_future_quotes, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_bucket_discovery:ai_two_pass_review_missing_fail_closed, swing_lifecycle_bucket_discovery:ai_two_pass_review_fail_closed_sim_auto_blocked, pattern_lab_ai_review_warning, pattern_lab_ai_review_ai_review_followup_required`.

## Workorder

- selected orders `106`, selected decisions `{"attach_existing_family": 93, "implement_now": 13}`, routes `{"ai_review_coverage_review": 1, "auto_patch_required": 5, "existing_family": 89, "implement_now": 4, "instrumentation_order": 3, "parent_conflict_exclusion_review": 1, "positive_source_only_review": 1, "review_ai_output": 1, "source_dimension_rollup": 1}`.
- pattern lab AI review source orders `5`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `warning`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-01.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-01.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-01.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-01.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-01.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-01.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-01.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-01.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-01.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-01.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-06-01.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-01.json` exists=true json_valid=true
