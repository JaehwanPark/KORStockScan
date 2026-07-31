# Tuning Performance Control Tower - 2026-07-31

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `0`
- positive_ev_not_due_until_next_preopen: `1`
- positive_ev_previous_policy_natural_match_0: `0`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `0`
- positive_ev_sample_floor_unknown_floor: `0`
- positive_ev_sample_floor_related_total: `0`
- positive_ev_sample_floor_scope: conversion_lane=`0` scope=`conversion_candidates` key_lineage=`0` scope=`lineage_rows` mismatch=`False`
- positive_ev_sample_floor_window: conversion_lane=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{}` key_lineage=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `183`
- observation_scope: runtime_policy_source_date=`2026-07-30` postclose_candidate_source_date=`2026-07-31` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`4` mismatch=`0` catalog_missing=`0` preopen_missing=`302` not_instrumented=`0`
- top_blocker_ranked: `key_lineage`; top_blocker_by_count=`key_lineage`
- top_ldm_bucket_blocker: `key_lineage`; submit_funnel_blocker_count=`6` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `source_gap_review_required`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `warning`.
- 근거: LDM `sim_auto_approved=1` (`+0`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `20`/`too_broad`, mtd `38`/`target_pass`, absorbed_sample `13639`, conflict_children `9`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target", "limit_down_watch_candidate_source_invalid", "limit_down_watch_candidate_source_quality_blocked", "limit_down_watch_source_blocked"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `44`, quiet_gap `245`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `324` (`+139`), surfaced `53` (`+27`), sim-auto `1` (`+0`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `1169` (`+1044`), joined `421` (`+338`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `40` (`+25`), complete `3` (`+0`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `9` (`-7`), exit `18` (`-5`), workorders `3`/`2`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0041`.
- Lifecycle join contract: blocked `false`, incomplete `735`, top reason `missing_holding`.
- Swing matrix: rows `None` (`n/a`), probe `None` (`n/a`), pending future quotes `None` (`n/a`).
- Swing bucket: sim-auto `None` (`n/a`), code-patch `None` (`n/a`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `0`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `26`, avg `-0.5131`, win-rate `0.6154`.
- Sim split sample `12`, avg `-0.8725`, win-rate `0.1667`.
- EV warnings: `trade_review_missing, performance_tuning_missing, pattern_lab_claude_stale, swing_pattern_lab_automation_missing, scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery_ev_missing, swing_lifecycle_decision_matrix_missing, swing_lifecycle_bucket_discovery_missing, codebase_performance_workorder_missing, pattern_lab_ai_review_warning, time_window_regime_counterfactual_missing, producer_gap_discovery_missing, stage_hook_workorder_discovery_missing, stage_hook_runtime_scaffold_missing, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `78`, selected decisions `{"attach_existing_family": 74, "implement_now": 4}`, routes `{"ai_review_coverage_review": 1, "existing_family": 70, "implement_now": 3, "join_gap_enrichment": 1, "positive_source_only_review": 1, "source_dimension_rollup": 1, "source_quality_warning_producer_fix": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 20, "needs_followup_workorder": 4, "root_cause_closed": 50}`, implementation_done `0`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `20`, root_cause_closed `50`, needs_followup `4`.
- pattern lab AI review source orders `3`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `4`.
- pattern lab currentness `pass`, AI review `warning`, propagation `warning`, producer gap `missing`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-31.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-31.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-31.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-07-31.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-31.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-07-31.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-07-31.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-31.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-31.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-07-31.json` exists=false json_valid=false
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-07-31.json` exists=false json_valid=false
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-31.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-31.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-31.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-07-31.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-07-31.json` exists=true json_valid=true
