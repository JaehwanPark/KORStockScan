# Tuning Performance Control Tower - 2026-08-10

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `0`
- positive_ev_not_due_until_next_preopen: `3`
- positive_ev_previous_policy_natural_match_0: `0`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked_known_floor: `2`
- positive_ev_sample_floor_unknown_floor: `0`
- positive_ev_sample_floor_related_total: `2`
- positive_ev_sample_floor_scope: conversion_lane=`2` scope=`conversion_candidates` key_lineage=`2` scope=`lineage_rows` mismatch=`False`
- positive_ev_sample_floor_window: conversion_lane=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2}` key_lineage=`same_day_source_bundle_plus_rolling_threshold_cycle_consumer` counts=`{'same_day_source_bundle_plus_rolling_threshold_cycle_consumer': 2}`
- positive_ev_sample_floor_basis: conversion_lane=`candidate_sample_vs_required_sample` key_lineage=`lineage_evidence_sample_vs_sample_floor`
- sim_priority_only: `22`
- observation_scope: runtime_policy_source_date=`2026-08-07` postclose_candidate_source_date=`2026-08-10` new_postclose_candidates_due_state=`not_due_until_next_preopen`
- key_lineage: pass=`8` mismatch=`0` catalog_missing=`0` preopen_missing=`0` not_instrumented=`0`
- top_blocker_ranked: `submit_drought`; top_blocker_by_count=`lifecycle_stage_underproduction`
- top_ldm_bucket_blocker: `lifecycle_stage_underproduction`; submit_funnel_blocker_count=`4` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `source_gap_review_required`
- bridge_policy_emit_state: `not_emitted_no_live_auto_ready_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `warning`, lifecycle_bucket_windows_status: `warning`.
- 근거: LDM `sim_auto_approved=0` (`+0`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`n/a`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `21`/`too_broad`, mtd `36`/`target_pass`, absorbed_sample `4761`, conflict_children `1`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_live_auto_ready_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `warning`, verifier_missing `[]`, handoff_warnings `["lifecycle_bucket_discovery_rolling5d_parent_granularity_not_target", "limit_down_watch_ordered_path_not_observed", "upper_limit_watch_cumulative_source_invalid", "upper_limit_watch_event_source_invalid", "upper_limit_watch_source_blocked"]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `25`, quiet_gap `340`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `396` (`+150`), surfaced `32` (`+6`), sim-auto `0` (`+0`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `1791` (`+941`), joined `1146` (`+988`), promote-ready `0` (`+0`).
- Lifecycle flow: buckets `32` (`+6`), complete `12` (`+10`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `14` (`+7`), exit `29` (`+9`), workorders `7`/`8`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0093`.
- Lifecycle join contract: blocked `false`, incomplete `1274`, top reason `missing_holding`.
- Swing matrix: rows `None` (`n/a`), probe `None` (`n/a`), pending future quotes `None` (`n/a`).
- Swing bucket: sim-auto `None` (`n/a`), code-patch `None` (`n/a`).
- Scalp sim control tower: approved `true`, policies `3`, sources `["lifecycle_bucket_discovery", "rising_missed_classifier_prior", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `1`, win-rate `0.0`, avg profit pct `0.0`, realized PnL KRW `0`.
- Real split sample `13`, avg `-0.1131`, win-rate `0.6154`.
- Sim split sample `26`, avg `-0.8815`, win-rate `0.4615`.
- EV warnings: `scalp_entry_adm:joined_sample_below_sample_floor, scalp_entry_adm:sim_post_sell_outcome_source_below_sample_floor, scalp_entry_adm:unknown_bucket_source_quality_gap, lifecycle_bucket_discovery:ai_review_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_, lifecycle_bucket_discovery:ai_review_selected_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_, lifecycle_bucket_discovery:sim_policy_review:ai_review_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_, lifecycle_bucket_discovery:sim_policy_review:ai_review_selected_evidence_authority_violation:lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_entry_ai_price_skip_order_stale_, pattern_lab_ai_review_warning`.

## Workorder

- selected orders `84`, selected decisions `{"attach_existing_family": 65, "implement_now": 19}`, routes `{"existing_family": 57, "implement_now": 18, "join_gap_enrichment": 1, "pattern_lab_ai_review_handoff_evidence": 5, "positive_source_only_review": 1, "source_dimension_rollup": 1, "source_quality_warning_producer_fix": 1}`.
- root-cause closure `{"handoff_closed_root_cause_open": 6, "needs_followup_workorder": 19, "root_cause_closed": 51}`, implementation_done `0`, artifact_regeneration_required `0`, handoff_closed_root_cause_open `6`, root_cause_closed `51`, needs_followup `19`.
- pattern lab AI review source orders `23`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `2`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `disabled_by_default`.

## Source

- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-10.json` exists=true json_valid=true
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-10.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-08-10.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-08-10.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-08-10.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-08-10.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-08-10.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-10.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-10.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-08-10.json` exists=false json_valid=false
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-08-10.json` exists=false json_valid=false
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-08-10.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-08-10.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-08-10.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-08-10.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-08-10.json` exists=true json_valid=true
