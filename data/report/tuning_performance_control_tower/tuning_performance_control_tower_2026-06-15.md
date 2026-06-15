# Tuning Performance Control Tower - 2026-06-15

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `2`
- positive_ev_not_due_until_next_preopen: `159`
- positive_ev_previous_policy_natural_match_0: `6`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `3`
- positive_ev_sample_floor_unknown_floor: `126`
- positive_ev_sample_floor_related_total: `129`
- positive_ev_sample_floor_scope: conversion_lane=`3` scope=`conversion_candidates` key_lineage=`10` scope=`lineage_rows` mismatch=`True`
- positive_ev_sample_floor_window: conversion_lane=`mixed_source_windows` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 3, 'source_report_window': 126}` key_lineage=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 15}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `121`
- observation_scope: runtime_policy_source_date=`2026-06-12` postclose_candidate_source_date=`2026-06-15` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`3` mismatch=`0` catalog_missing=`0` preopen_missing=`85` not_instrumented=`0`
- top_blocker_ranked: `sample_floor`; top_blocker_by_count=`sample_floor`
- top_ldm_bucket_blocker: `sample_floor`; submit_funnel_blocker_count=`6` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `sim_progress_no_live_bucket`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_auto_approved=5` (`+5`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `18` (`+14`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `53`/`target_pass`, mtd `41`/`target_pass`, absorbed_sample `124527`, conflict_children `21`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["active_sim_priority_preopen_handoff_pending"]`.
- Runtime gap audit: status `pass`, directives `1`, source_dimension_gap `64`, quiet_gap `400`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `500` (`+0`), surfaced `133` (`-18`), sim-auto `5` (`+5`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `19534` (`+311`), joined `17684` (`+1673`), promote-ready `1` (`+1`).
- Lifecycle flow: buckets `120` (`-21`), complete `79` (`-15`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `36` (`-2`), exit `54` (`+5`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0044`.
- Lifecycle join contract: blocked `false`, incomplete `17717`, top reason `missing_holding`.
- Swing matrix: rows `68551` (`+24787`), probe `63487` (`+24135`), pending future quotes `3425` (`+467`).
- Swing bucket: sim-auto `18` (`+14`), code-patch `52` (`+1`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `2`, win-rate `0.0`, avg profit pct `-0.58`, realized PnL KRW `-20110`.
- Real split sample `0`, avg `None`, win-rate `None`.
- Sim split sample `1395`, avg `-1.2471`, win-rate `0.2344`.
- EV warnings: `scalp_entry_adm:unknown_bucket_source_quality_gap, lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered, pattern_lab_ai_review_warning, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `160`, selected decisions `{"attach_existing_family": 144, "defer_evidence": 8, "design_family_candidate": 5, "reject": 3}`, routes `{"ai_review_coverage_review": 1, "attach_existing_family": 2, "auto_family_candidate": 4, "design_family_candidate": 1, "existing_family": 136, "pattern_lab_ai_review_handoff_evidence": 2, "performance_optimization_order": 12, "positive_source_only_review": 1, "source_dimension_rollup": 1}`.
- pattern lab AI review source orders `4`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `3`.
- pattern lab currentness `warning`, AI review `warning`, propagation `warning`, producer gap `pass`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-06-15.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-15.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-15.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-15.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-15.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-06-15.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-15.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-15.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-15.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-15.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-15.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-15.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-15.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-15.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-06-15.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-15.json` exists=true json_valid=true
