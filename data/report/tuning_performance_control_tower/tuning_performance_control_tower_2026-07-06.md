# Tuning Performance Control Tower - 2026-07-06

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `1`
- positive_ev_not_due_until_next_preopen: `146`
- positive_ev_previous_policy_natural_match_0: `2`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `1`
- positive_ev_sample_floor_unknown_floor: `98`
- positive_ev_sample_floor_related_total: `99`
- positive_ev_sample_floor_scope: conversion_lane=`1` scope=`conversion_candidates` key_lineage=`3` scope=`lineage_rows` mismatch=`True`
- positive_ev_sample_floor_window: conversion_lane=`mixed_source_windows` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 1, 'source_report_window': 98}` key_lineage=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 4}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `211`
- observation_scope: runtime_policy_source_date=`2026-07-03` postclose_candidate_source_date=`2026-07-06` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`7` mismatch=`0` catalog_missing=`0` preopen_missing=`136` not_instrumented=`0`
- top_blocker_ranked: `sample_floor`; top_blocker_by_count=`sample_floor`
- top_ldm_bucket_blocker: `sample_floor`; submit_funnel_blocker_count=`0` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `daily_detected_cumulative_missing`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `warning`.
- 근거: LDM `sim_auto_approved=5` (`+3`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `42` (`+6`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `42`/`target_pass`, mtd `29`/`too_broad`, absorbed_sample `20761`, conflict_children `9`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `False`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["active_sim_priority_preopen_handoff_pending", "ai_watching_score_smoothing_diagnostic_followup_open", "lifecycle_bucket_discovery_mtd_parent_granularity_not_target", "quote_consistency_required_fields_excluded", "quote_consistency_source_missing", "swing_active_arm_priority_preopen_handoff_pending", "swing_active_arm_priority_runtime_observation_missing"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `61`, quiet_gap `410`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `500` (`+0`), surfaced `78` (`+2`), sim-auto `5` (`+3`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `3054` (`-2034`), joined `1164` (`-1997`), promote-ready `0` (`-1`).
- Lifecycle flow: buckets `67` (`-3`), complete `13` (`+6`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `24` (`+0`), exit `42` (`+2`), workorders `5`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0048`.
- Lifecycle join contract: blocked `false`, incomplete `2714`, top reason `missing_holding`.
- Swing matrix: rows `14120` (`+612`), probe `0` (`+0`), pending future quotes `3910` (`-169`).
- Swing bucket: sim-auto `42` (`+6`), code-patch `67` (`-8`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `12`, win-rate `66.67`, avg profit pct `-0.13`, realized PnL KRW `-24453`.
- Real split sample `148`, avg `0.1816`, win-rate `0.5608`.
- Sim split sample `96`, avg `-1.3031`, win-rate `0.3958`.
- EV warnings: `scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, lifecycle_bucket_discovery:source_contract_drift_warning, lifecycle_bucket_discovery:source_contract_drift_warning, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered, swing_lifecycle_decision_matrix:swing_intraday_live_equiv_probe_missing, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered, pattern_lab_ai_review_warning, producer_gap_discovery_ai_review_followup_required`.

## Workorder

- selected orders `105`, selected decisions `{"attach_existing_family": 95, "defer_evidence": 2, "implement_now": 8}`, routes `{"ai_review_coverage_review": 1, "auto_patch_required": 4, "existing_family": 92, "implement_now": 2, "instrumentation_order": 2, "positive_source_only_review": 1, "review_ai_output": 1, "source_dimension_rollup": 1, "source_quality_warning_producer_fix": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 20, "implementation_done": 1, "needs_followup_workorder": 8, "root_cause_closed": 70}`, implementation_done `1`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `20`, root_cause_closed `70`, needs_followup `8`.
- pattern lab AI review source orders `2`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `warning`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-07-06.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-07-06.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-07-06.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-07-06.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-07-06.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-07-06.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-07-06.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-07-06.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-07-06.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-07-06.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-07-06.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-07-06.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-07-06.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-07-06.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-07-06.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-07-06.json` exists=true json_valid=true
