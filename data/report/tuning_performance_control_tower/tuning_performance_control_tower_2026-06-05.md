# Tuning Performance Control Tower - 2026-06-05

## Conversion First

- real_conversion_queue: `0`
- positive_ev_runtime_observed: `0`
- positive_ev_not_due_until_next_preopen: `26`
- positive_ev_previous_policy_natural_match_0: `4`
- positive_ev_real_conversion_queue: `0`
- positive_ev_sample_floor_blocked: `15`
- sim_priority_only: `31`
- observation_scope: runtime_policy_source_date=`-` postclose_candidate_source_date=`-` new_postclose_candidates_due_state=`-`
- key_lineage: pass=`3` mismatch=`0` catalog_missing=`0` preopen_missing=`0` not_instrumented=`0`
- top_blocker_overall: `submit_drought`
- top_ldm_bucket_blocker: `env_mapping`; submit_funnel_blocker_count=`6` submit_drought_is_ldm_bucket_blocker=`False`

## 판정

- 판정: `sim_progress_no_live_bucket`
- bridge_policy_emit_state: `not_emitted_no_complete_lifecycle_flow`, promotion_window: `mtd`, verifier_status: `pass`, lifecycle_bucket_windows_status: `pass`.
- 근거: LDM `sim_auto_approved=165` (`+79`), `live_auto_apply_ready=0` (`+0`), swing sim-auto `0` (`+0`).
- 실현손익 해석: `real_pnl_is_tuning_performance=false` (post_apply_attribution_not_ready:pending_applied_cohort).
- 다음 액션: 내일은 `live_auto_apply_ready`, `post_apply_attribution`, `pending_future_quote_count`, selected workorder backlog만 먼저 본다.

## LDM 승격/후보

- Live-ready split: daily_discovery `0`, promotion_window `0`, bridge_ready `0`.
- Parent bucket: daily parent_granularity_status `34`/`target_pass`, mtd `48`/`target_pass`, absorbed_sample `14597`, conflict_children `7`.
- Bridge/verifier: greenfield_policy_emit_state `not_emitted_no_complete_lifecycle_flow`, greenfield_policy_emit_blocker `no_live_auto_ready_lifecycle_flow`, promotion_contract_passed `True`, verifier_status `pass`, verifier_missing `[]`, handoff_warnings `[]`.
- Runtime gap audit: status `pass`, directives `0`, source_dimension_gap `46`, quiet_gap `199`, quiet_gap_directives `0`.
- Source freshness: status `pass`, stale_pairs `0`, warning `-`.
- Lifecycle bucket: candidates `500` (`+66`), surfaced `255` (`+107`), sim-auto `165` (`+79`), live-ready `0` (`+0`).
- Lifecycle matrix: rows `13164` (`+10606`), joined `12500` (`+10083`), promote-ready `1` (`+1`).
- Lifecycle flow: buckets `85` (`+23`), complete `56` (`+52`), runtime `0` (`+0`), workorders `20` (`+0`).
- Holding/exit buckets: holding `32` (`+9`), exit `48` (`-3`), workorders `10`/`10`.
- Lifecycle identity: missing `0` (`+0`), join_rate `1.0`, complete_flow_rate `0.0046`.
- Lifecycle join contract: blocked `false`, incomplete `12238`, top reason `missing_submit`.
- Swing matrix: rows `76232` (`+57690`), probe `75250` (`+57108`), pending future quotes `982` (`+582`).
- Swing bucket: sim-auto `0` (`+0`), code-patch `0` (`+0`).
- Scalp sim control tower: approved `true`, policies `2`, sources `["lifecycle_bucket_discovery", "scalp_sim_scale_in_window_approval"]`, bridge live-ready summary `0`.

## EV 해석

- Daily completed trades `1`, win-rate `0.0`, avg profit pct `-2.52`, realized PnL KRW `-3184`.
- Real split sample `38`, avg `-0.5997`, win-rate `0.5`.
- Sim split sample `888`, avg `-1.1644`, win-rate `0.2646`.
- EV warnings: `scalp_entry_adm:unknown_bucket_source_quality_gap, swing_strategy_discovery:pending_future_quotes, swing_strategy_discovery:sample_floor_not_met, swing_strategy_discovery:clean_tuning_baseline_swing_discovery_lookback_filtered, swing_lifecycle_decision_matrix:pending_future_quotes, swing_lifecycle_decision_matrix:clean_tuning_baseline_swing_discovery_lookback_filtered, pattern_lab_ai_review_warning, pattern_lab_ai_review_ai_review_followup_required`.

## Workorder

- selected orders `106`, selected decisions `{"attach_existing_family": 106}`, routes `{"ai_review_coverage_review": 1, "existing_family": 102, "parent_conflict_exclusion_review": 1, "positive_source_only_review": 1, "source_dimension_rollup": 1}`.
- pattern lab AI review source orders `0`, pattern lab currentness source orders `0`.
- 해석: `implement_now`는 자동 repo 수정이 아니라 `runtime_effect=false` intake다. 사용자가 Codex 구현을 지시한 경우에만 코드 작업이다.

## Runtime Summary

- runtime mutation allowed `false`; scalping selected auto-bounded-live `1`.
- pattern lab currentness `pass`, AI review `warning`, propagation `pass`, producer gap `pass`.

## Source

- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-06-05.json` exists=true json_valid=true
- runtime_approval_summary: `/home/ubuntu/KORStockScan/data/report/runtime_approval_summary/runtime_approval_summary_2026-06-05.json` exists=true json_valid=true
- runtime_apply_bridge: `/home/ubuntu/KORStockScan/data/report/runtime_apply_bridge/runtime_apply_bridge_2026-06-05.json` exists=true json_valid=true
- runtime_apply_gap_audit: `/home/ubuntu/KORStockScan/data/report/runtime_apply_gap_audit/runtime_apply_gap_audit_2026-06-05.json` exists=true json_valid=true
- key_lineage_ledger: `/home/ubuntu/KORStockScan/data/report/key_lineage_ledger/key_lineage_ledger_2026-06-05.json` exists=true json_valid=true
- conversion_lane: `/home/ubuntu/KORStockScan/data/report/conversion_lane/conversion_lane_2026-06-05.json` exists=true json_valid=true
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-06-05.json` exists=true json_valid=true
- lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-06-05.json` exists=true json_valid=true
- swing_lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_decision_matrix/swing_lifecycle_decision_matrix_2026-06-05.json` exists=true json_valid=true
- swing_lifecycle_bucket_discovery: `/home/ubuntu/KORStockScan/data/report/swing_lifecycle_bucket_discovery/swing_lifecycle_bucket_discovery_2026-06-05.json` exists=true json_valid=true
- code_improvement_workorder: `/home/ubuntu/KORStockScan/data/report/code_improvement_workorder/code_improvement_workorder_2026-06-05.json` exists=true json_valid=true
- threshold_apply: `/home/ubuntu/KORStockScan/data/threshold_cycle/apply_plans/threshold_apply_2026-06-05.json` exists=true json_valid=true
- threshold_cycle_postclose_verification: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_postclose_verification/threshold_cycle_postclose_verification_2026-06-05.json` exists=true json_valid=true
- scalp_sim_auto_approval: `/home/ubuntu/KORStockScan/data/threshold_cycle/sim_auto_approvals/scalp_sim_auto_approval_2026-06-05.json` exists=true json_valid=true
- scalp_sim_policy_catalog: `/home/ubuntu/KORStockScan/data/threshold_cycle/scalp_sim_policies/scalp_sim_policy_catalog_2026-06-05.json` exists=true json_valid=true
