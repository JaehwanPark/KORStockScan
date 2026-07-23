# Tuning Performance Control Tower - 2026-07-23

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `0`
- positive_ev_not_due_until_next_preopen: `128`
- positive_ev_previous_policy_natural_match_0: `0`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `0`
- positive_ev_sample_floor_unknown_floor: `80`
- positive_ev_sample_floor_related_total: `80`
- positive_ev_sample_floor_scope: conversion_lane=`0` scope=`conversion_candidates` key_lineage=`0` scope=`lineage_rows` mismatch=`False`
- positive_ev_sample_floor_window: conversion_lane=`source_report_window` counts=`{'source_report_window': 80}` key_lineage=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `301`
- observation_scope: runtime_policy_source_date=`2026-07-22` postclose_candidate_source_date=`2026-07-23` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`2` mismatch=`0` catalog_missing=`0` preopen_missing=`223` not_instrumented=`0`
- top_blocker_ranked: `sample_floor`; top_blocker_by_count=`sample_floor`
- top_ldm_bucket_blocker: `sample_floor`; submit_funnel_blocker_count=`0` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `daily_detected_cumulative_missing`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `warning`.
- 근거: LDM `sim_auto_approved=1` (`-1`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `47` (`+6`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `17`/`too_broad`, mtd `44`/`target_pass`, absorbed_sample `33274`, conflict_children `13`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["ai_watching_score_smoothing_diagnostic_followup_open", "lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `29`, quiet_gap `168`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `220` (`-81`), surfaced `42` (`-11`), sim-auto `1` (`-1`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `353` (`-432`), joined `106` (`-295`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `30` (`-9`), complete `7` (`-2`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `10` (`-4`), exit `19` (`-8`), workorders `0`/`5`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0345`.
- Lifecycle join contract: blocked `false`, incomplete `196`, top reason `missing_holding`.
- Swing matrix: rows `25984` (`+869`), probe `0` (`+0`), pending future quotes `6665` (`+425`).
- Swing bucket: sim-auto `47` (`+6`), code-patch `85` (`+16`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `9`, win-rate `55.56`, avg profit pct `-0.59`, realized PnL KRW `-26747`.
- Real split sample `54`, avg `-0.187`, win-rate `0.537`.
- Sim split sample `13`, avg `-1.1131`, win-rate `0.1538`.
- EV warnings: `scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered, swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered, pattern_lab_propagation_audit_warning`.

## Workorder

- selected orders `172`, selected decisions `{"attach_existing_family": 171, "implement_now": 1}`, routes `{"ai_review_coverage_review": 1, "existing_family": 169, "positive_source_only_review": 1, "source_quality_warning_producer_fix": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 20, "implementation_done": 1, "needs_followup_workorder": 1, "root_cause_closed": 148}`, implementation_done `1`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `20`, root_cause_closed `148`, needs_followup `1`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `4`.
- pattern lab currentness `pass`, AI review `pass`, propagation `warning`, producer gap `pass`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-23.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-23.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-23.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-07-23.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-23.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-07-23.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-07-23.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-23.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-23.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-07-23.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-07-23.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-23.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-23.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-23.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-07-23.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-07-23.json` exists=true json_valid=true
