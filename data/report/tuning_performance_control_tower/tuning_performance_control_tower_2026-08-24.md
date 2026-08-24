# Tuning Performance Control Tower - 2026-08-24

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
- sim_priority_only: `31`
- observation_scope: runtime_policy_source_date=`2026-08-21` postclose_candidate_source_date=`2026-08-24` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`1` mismatch=`0` catalog_missing=`0` preopen_missing=`0` not_instrumented=`0`
- top_blocker_ranked: `submit_drought`; top_blocker_by_count=`lifecycle_stage_underproduction`
- top_ldm_bucket_blocker: `lifecycle_stage_underproduction`; submit_funnel_blocker_count=`4` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `observe_only_no_new_tuning_progress`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_policy_approved_total=0` (direct=`0`, lifecycle_flow=`0`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `23`/`too_broad`, mtd `31`/`target_pass`, absorbed_sample `17431`, conflict_children `4`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["limit_down_watch_ordered_path_not_observed"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `33`, quiet_gap `307`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `369` (`+28`), surfaced `49` (`+5`), sim-policy-total `0` (direct=`0`, flow=`0`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `1116` (`-1510`), joined `411` (`-252`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `49` (`+5`), complete `19` (`+8`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `22` (`+8`), exit `35` (`+9`), workorders `7`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0374`.
- Lifecycle join contract: blocked `false`, incomplete `489`, top reason `missing_holding`.
- Swing matrix: rows `None` (`n/a`), probe `None` (`n/a`), pending future quotes `None` (`n/a`).
- Swing bucket: sim-auto `None` (`n/a`), code-patch `None` (`n/a`).
- Scalp sim control tower: approved `false`, policies `2`, sources `["lifecycle_bucket_discovery", "rising_missed_classifier_prior"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `8`, win-rate `62.5`, avg profit pct `-0.6411`, realized PnL KRW `-76`.
- Real split sample `8`, avg `-0.6411`, win-rate `0.625`.
- Sim split sample `19`, avg `-0.5347`, win-rate `0.3158`.
- EV warnings: `scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:sim_post_sell_outcome_source_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, codebase_performance_workorder_missing, time_window_regime_counterfactual_missing, producer_gap_discovery_missing, stage_hook_workorder_discovery_missing, stage_hook_runtime_scaffold_missing`.

## Workorder

- selected orders `63`, selected decisions `{"attach_existing_family": 63}`, routes `{"ai_review_coverage_review": 1, "existing_family": 58, "join_gap_enrichment": 1, "positive_source_only_review": 1, "source_dimension_rollup": 1, "source_quality_raw_row_exclusion_revalidated_closed": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 4, "implementation_done": 1, "root_cause_closed": 53}`, implementation_done `1`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `4`, root_cause_closed `53`, needs_followup `0`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `pass`, propagation `pass`, producer gap `disabled_by_default`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-24.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-24.json` exists=true json_valid=true
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-08-24_postclose.json` exists=true json_valid=true
- threshold_cycle_ai_review: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ai_review/threshold_cycle_ai_review_2026-08-24_postclose.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-08-24.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-08-24.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-24.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-08-24.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-08-24.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-24.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-24.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-08-24.json` exists=false json_valid=false
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-08-24.json` exists=false json_valid=false
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-24.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-24.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-24.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-08-24.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-08-24.json` exists=true json_valid=true
