# Tuning Performance Control Tower - 2026-06-04

## Conversion First

- real_conversion_queue: `3`
- sim_priority_only: `71`
- key_lineage: pass=`4` mismatch=`0` catalog_missing=`12` preopen_missing=`0` not_instrumented=`0`
- top_blocker: `key_lineage`

## 판정

- 판정: `postclose_verifier_blocked`
- bridge_policy_emit_state: `not_emitted_no_complete_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `fail`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_auto_approved=86` (`n/a`), `live_auto_apply_ready=0` (`n/a`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `43`/`target_pass`, mtd `43`/`target_pass`, absorbed_sample `2303`, conflict_children `2`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_complete_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `fail`, verifier_missing `[]`, handoff_warnings `["swing_active_arm_priority_runtime_observation_missing"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `94`, quiet_gap `212`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `434` (`n/a`), surfaced `148` (`n/a`), sim-auto `86` (`n/a`), live-ready `0` (`n/a`).
- Lifecycle matrix: rows `2558` (`n/a`), joined `2417` (`n/a`), promote-ready `0` (`n/a`).
- Lifecycle flow: buckets `62` (`n/a`), complete `4` (`n/a`), runtime `0` (`n/a`), workorders `20` (`n/a`).
- Holding/exit buckets: holding `23` (`n/a`), exit `51` (`n/a`), workorders `7`/`10`.
- Lifecycle identity: missing `0` (`n/a`), join_rate `1.0`, complete_flow_rate `0.0017`.
- Lifecycle join contract: blocked `false`, incomplete `2299`, top reason `missing_submit`.
- Swing matrix: rows `18542` (`n/a`), probe `18142` (`n/a`), pending future quotes `400` (`n/a`).
- Swing bucket: sim-auto `0` (`n/a`), code-patch `0` (`n/a`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `8`, win-rate `25.0`, avg profit pct `-1.41`, realized PnL KRW `-13049`.
- Real split sample `40`, avg `-0.5948`, win-rate `0.5`.
- Sim split sample `737`, avg `-1.1485`, win-rate `0.2741`.
- EV warnings: `scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, scalp_entry_adm:prompt_context_not_loaded, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:sample_floor_not_met, swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered, pattern_lab_ai_review_warning, pattern_lab_ai_review_ai_review_followup_required`.

## Workorder

- selected orders `100`, selected decisions `{"attach_existing_family": 79, "defer_evidence": 1, "implement_now": 20}`, routes `{"ai_review_coverage_review": 1, "existing_family": 72, "instrumentation_order": 20, "parent_conflict_exclusion_review": 1, "pattern_lab_ai_review_followup_evidence": 1, "pattern_lab_ai_review_handoff_evidence": 3, "positive_source_only_review": 1, "source_dimension_rollup": 1}`.
- pattern lab AI review source orders `6`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `pass`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-04.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-04.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-04.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-04.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-06-04.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-04.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-04.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-04.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-04.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-04.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-04.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-04.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-04.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-06-04.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-04.json` exists=true json_valid=true
