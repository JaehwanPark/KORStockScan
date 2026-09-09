# Tuning Performance Control Tower - 2026-09-09

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `0`
- positive_ev_not_due_until_next_preopen: `0`
- positive_ev_previous_policy_natural_match_0: `0`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `0`
- positive_ev_sample_floor_unknown_floor: `0`
- positive_ev_sample_floor_related_total: `0`
- positive_ev_sample_floor_scope: conversion_lane=`0` scope=`conversion_candidates` key_lineage=`0` scope=`lineage_rows` mismatch=`False`
- positive_ev_sample_floor_window: conversion_lane=`source_report_window` counts=`{}` key_lineage=`source_report_window` counts=`{}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `0`
- observation_scope: runtime_policy_source_date=`2026-09-08` postclose_candidate_source_date=`2026-09-09` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`0` mismatch=`0` catalog_missing=`0` preopen_missing=`0` not_instrumented=`0`
- top_blocker_ranked: `submit_drought`; top_blocker_by_count=`submit_drought`
- top_ldm_bucket_blocker: `none`; submit_funnel_blocker_count=`4` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `source_gap_review_required`
- bridge_policy_emit_state: `-`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `retired`.
- 근거: LDM `sim_policy_approved_total=0` (direct=`0`, lifecycle_flow=`0`), `live_auto_apply_ready=0` (`n/a`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `0`/`None`, mtd `0`/`None`, absorbed_sample `0`, conflict_children `0`.
- Bridge/verifier: greenfield_policy_emit_state `-`, greenfield_policy_emit_blocker `-`, promotion_contract_passed `False`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["limit_down_watch_ordered_path_not_observed", "microstructure_diagnostic:warning"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `0`, quiet_gap `0`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `None` (`n/a`), surfaced `None` (`n/a`), sim-policy-total `None` (direct=`None`, flow=`None`), live-ready `None` (`n/a`).
- Lifecycle matrix: rows `None` (`n/a`), joined `None` (`n/a`), promote-ready `None` (`n/a`).
- Lifecycle flow: buckets `None` (`n/a`), complete `None` (`n/a`), runtime `None` (`n/a`), workorders `None` (`n/a`).
- Holding/exit buckets: holding `None` (`n/a`), exit `None` (`n/a`), workorders `None`/`None`.
- Lifecycle identity: missing `None` (`n/a`), join_rate `None`, complete_flow_rate `None`.
- Lifecycle join contract: blocked `none`, incomplete `None`, top reason `None`.
- Swing matrix: rows `None` (`n/a`), probe `None` (`n/a`), pending future quotes `None` (`n/a`).
- Swing bucket: sim-auto `None` (`n/a`), code-patch `None` (`n/a`).
- Scalp sim control tower: approved `false`, policies `0`, sources `[]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `None`.
- Realized PnL status: `count_reconciled_snapshot_diagnostic_not_cost_verified`; missing/mismatched PnL is not measured zero profit.
- Real split sample `0`, avg `None`, win-rate `None`.
- Sim split sample `21`, avg `-0.809`, win-rate `0.4762`.
- EV warnings: `microstructure_reaction_context:diagnostic_contract:evaluation_venue_missing_or_conflicting, microstructure_reaction_context:diagnostic_contract:evaluation_anchor_contract_missing, microstructure_reaction_context:clean_baseline:daily_rollup_missing_or_stale_dates_excluded, microstructure_reaction_context:clean_baseline:exact_attempt_time_outcome_coverage_incomplete, pattern_lab_ai_review_warning, pattern_lab_ai_review_ai_review_followup_required`.

## Workorder

- selected orders `33`, selected decisions `{"attach_existing_family": 10, "defer_evidence": 12, "implement_now": 11}`, routes `{"existing_family": 10, "instrumentation_order": 10, "maintenance_review": 2, "pattern_lab_ai_review_followup_evidence": 10, "source_quality_warning_producer_fix": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 4, "implementation_done": 5, "needs_followup_workorder": 11, "root_cause_closed": 1}`, implementation_done `5`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `4`, root_cause_closed `1`, needs_followup `11`.
- pattern lab AI review source orders `10`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 실전 권한이 아닌 source-only intake다. 명시적 구현 또는 장후 모니터링 지시의 허용 범위에서 review/fix 후 처리한다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `1`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `disabled_by_default`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-09-09.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-09-09.json` exists=true json_valid=true
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-09-09_postclose.json` exists=true json_valid=true
- threshold_cycle_ai_review: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-09-09_postclose.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-09-09.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-09-09.json` exists=false json_valid=false
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-09-09.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-09-09.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-09-09.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-09-09.json` exists=false json_valid=false
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-09-09.json` exists=false json_valid=false
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-09-09.json` exists=false json_valid=false
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-09-09.json` exists=false json_valid=false
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-09-09.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-09-09.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-09-09.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-09-09.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-09-09.json` exists=true json_valid=true

<!-- POSTCLOSE_RECOMMENDATION_INTAKE_START -->
## 추천 전수 전달 대사

- source-date: `2026-09-09`; status: `warning`
- native rows SHA256: `1d01fac2e3773938fb4f4961b5f0a187ddcd6c0eb5591f273a79b2a0da398210`
- counts: `{"already_implemented_verified_eligible": 0, "already_implemented_verified_nonrequest": 0, "blocked_external_dependency": 0, "blocked_external_dependency_nonrequest": 0, "blocked_missing_evidence": 11, "blocked_missing_evidence_nonrequest": 3, "deferred": 32, "eligible_actionable_open": 0, "eligible_runtime_effect_false_total": 11, "implement_now_unaccounted_count": 0, "implementation_requested_total": 11, "implemented_pass1": 0, "implemented_pass2": 0, "intake_total": 72, "intake_unaccounted_count": 0, "invalid_or_missing_authority_nonrequest": 0, "invalid_or_missing_authority_total": 0, "nonimplementation_total": 61, "observed_no_patch": 23, "rejected": 3, "user_authority_nonrequest": 0, "user_authority_total": 0}`
- dispositions: `{"blocked_missing_evidence": 14, "deferred": 32, "observed_no_patch": 23, "rejected": 3}`
- 운영 terminal, 구현 fixed-point, PREOPEN 선택, PID 소비, 경제성은 별도 상태다.

| Owner | Native recommendation dispositions |
| --- | --- |
| low_price_two_leg_expanded_candidate_research | `{"blocked_missing_evidence": 2, "deferred": 7}` |
| machine_microstructure_attribution | `{"observed_no_patch": 1}` |
| main | `{"blocked_missing_evidence": 11, "deferred": 18, "observed_no_patch": 22}` |
| widget_collector_expansion_recommendation | `{"deferred": 7}` |
| widget_symbol_signal_policy_research | `{"blocked_missing_evidence": 1, "rejected": 3}` |
<!-- POSTCLOSE_RECOMMENDATION_INTAKE_END -->


## PREOPEN 계획과 선택 근거

- planned `18` / manifest-selected `18`; evidence `manifest_selection_receipt_consistent`.
- plan-only `['entry_opportunity_recheck_runtime']` / manifest-only `['entry_cancel_wait_runtime']`.
- 명시적 OFF/선택 차이의 원문 근거는 JSON `selected_runtime.selection_differences`에 보존한다.
- PID 소비·현재 런타임 재검증·비용 후 경제성은 이 요약으로 입증하지 않는다.
