# Code Improvement Workorder - 2026-08-04

## 목적

- Postclose 자동화가 생성한 `code_improvement_order`를 Codex 실행용 작업지시서로 변환한다.
- 입력은 scalping pattern lab automation, swing lifecycle improvement automation, swing pattern lab automation을 함께 포함할 수 있다.
- 이 문서는 repo/runtime을 직접 변경하지 않는다. 사용자가 이 문서를 Codex 세션에 넣고 구현을 요청하는 지점만 사람 개입으로 남긴다.
- 구현 후 자동화체인 재투입은 다음 postclose report, threshold calibration, daily EV report가 담당한다.

## Source

- pattern_lab_automation: `/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-08-04.json`
- swing_improvement_automation: `-`
- swing_pattern_lab_automation: `-`
- swing_strategy_discovery_ev: `-`
- swing_lifecycle_decision_matrix: `-`
- swing_lifecycle_bucket_discovery: `-`
- threshold_cycle_ev: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_ev/threshold_cycle_ev_2026-08-04.json`
- lifecycle_decision_matrix: `/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-04.json`
- threshold_cycle_calibration: `/home/ubuntu/KORStockScan/data/report/threshold_cycle_calibration/threshold_cycle_calibration_2026-08-04_postclose.json`
- pipeline_event_verbosity: `/home/ubuntu/KORStockScan/data/report/pipeline_event_verbosity/pipeline_event_verbosity_2026-08-04.json`
- observation_source_quality_audit: `/home/ubuntu/KORStockScan/data/report/observation_source_quality_audit/observation_source_quality_audit_2026-08-04.json`
- ai_decision_action_outcome_calibration: `/home/ubuntu/KORStockScan/data/report/ai_decision_action_outcome_calibration/ai_decision_action_outcome_calibration_2026-08-04.json`
- codebase_performance_workorder: `-`
- pattern_lab_currentness_audit: `/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-04.json`
- pattern_lab_ai_review: `/home/ubuntu/KORStockScan/data/report/pattern_lab_ai_review/pattern_lab_ai_review_2026-08-04.json`
- producer_gap_discovery: `-`
- stage_hook_workorder_discovery: `-`
- stage_hook_runtime_scaffold: `-`
- buy_funnel_sentinel: `/home/ubuntu/KORStockScan/data/report/buy_funnel_sentinel/buy_funnel_sentinel_2026-08-04.json`
- microstructure_reaction_context: `/home/ubuntu/KORStockScan/data/report/microstructure_reaction_context/microstructure_reaction_context_2026-08-04.json`
- generated_at: `2026-08-04T21:29:10+09:00`
- generation_id: `2026-08-04-b9f46d6c6ab5`
- source_hash: `b9f46d6c6ab554c22cc16767bf6c642bc006ef90d3bb0e7796b16e51890230b0`

## 운영 원칙

- `runtime_effect=false` order만 구현 대상으로 본다.
- fallback 재개, shadow 재개, safety guard 우회는 구현하지 않는다.
- runtime 영향이 생길 수 있는 변경은 feature flag, threshold family metadata, provenance, safety guard를 같이 닫는다.
- 새 family는 `allowed_runtime_apply=false`에서 시작하고, 구현/테스트/guard 완료 후에만 auto_bounded_live 후보가 될 수 있다.
- 구현 후에는 관련 테스트와 parser 검증을 실행하고, 다음 postclose daily EV에서 metric을 확인한다.
- 같은 날짜 workorder를 재생성하면 `generation_id`와 `lineage` diff로 신규/삭제/판정변경 order를 먼저 확인한다.

## 2-Pass 실행 기준

- Pass 1: `implement_now` 중 instrumentation/report/provenance 구현만 먼저 수행한다.
- Regeneration: 관련 postclose report와 이 workorder를 재생성하고 `lineage` diff를 확인한다.
- Pass 2: 재생성 후 새로 생긴 `runtime_effect=false` order만 추가 구현한다.
- Final freeze: `generation_id`, `source_hash`, 신규/삭제/판정변경 order를 최종 보고에 남긴다.
- 권장 지시문: `lifecycle bucket discovery hook gap은 자동 patch 후보를 만들고, self code review + fix 2-pass + targeted tests 통과 전에는 runtime env로 소비하지 않는다.`

## Snapshot Lineage

- previous_exists: `True`
- previous_generation_id: `2026-08-04-d9a3be3f39b7`
- previous_source_hash: `d9a3be3f39b758d07a67a7bf42fed01a0c14043440b00ff8742af8f4bc501e84`
- new_order_ids: `['order_ai_threshold_miss_ev_recovery', 'order_latency_guard_miss_ev_recovery', 'order_one_share_threshold_strength_momentum_vpw_entry_hook_review', 'order_panic_sell_defense_lifecycle_transition_pack', 'order_partial_only_표류_전용_timeout_report_only', 'order_rising_missed_classifier_prior_bridge', 'order_rising_missed_classifier_prior_feedback_bridge', 'order_rising_missed_scout_loss_filter', 'order_rising_missed_scout_post_sell_bridge', 'order_rising_missed_scout_take_profit_capture_review', 'order_scale_in_split_order_plan_contract_gap', 'order_split_entry_rebase_수량_정합성_report_only_감사']`
- removed_order_ids: `[]`
- decision_changed_order_ids: `[]`

## Summary

- source_order_count: `97`
- scalping_source_order_count: `10`
- swing_source_order_count: `0`
- swing_entry_bottleneck_primary: `None`
- swing_entry_bottleneck_selected: `False`
- swing_lab_source_order_count: `0`
- swing_strategy_discovery_source_order_count: `0`
- swing_lifecycle_matrix_source_order_count: `0`
- swing_lifecycle_bucket_discovery_source_order_count: `0`
- pattern_lab_currentness_source_order_count: `0`
- pattern_lab_ai_review_source_order_count: `1`
- threshold_ev_source_order_count: `9`
- entry_hurdle_backtest_source_order_count: `0`
- microstructure_reaction_context_source_order_count: `0`
- lifecycle_submit_bucket_source_order_count: `0`
- lifecycle_holding_exit_bucket_source_order_count: `7`
- pipeline_event_verbosity_source_order_count: `0`
- observation_source_quality_source_order_count: `0`
- codebase_performance_source_order_count: `0`
- buy_funnel_sentinel_source_order_count: `6`
- entry_submit_drought_selected: `True`
- entry_submit_drought_handoff_missing: `False`
- panic_lifecycle_source_order_count: `1`
- selected_order_count: `91`
- non_selected_order_count: `6`
- operator_workload_summary: `{'implementation_required_count': 0, 'existing_family_attribution_count': 86, 'visibility_only_count': 5, 'other_selected_count': 0, 'root_cause_open_count': 21, 'selected_total_count': 91, 'category_count_reconciled': True, 'runtime_effect_true_count': 0}`
- source_decision_counts: `{'attach_existing_family': 92, 'design_family_candidate': 3, 'defer_evidence': 1, 'reject': 1}`
- selected_decision_counts: `{'attach_existing_family': 91}`
- selected_route_counts: `{'existing_family': 86, 'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'source_quality_gap': 1}`
- selected_implement_now_route_count: `0`
- selected_runtime_effect_false_count: `91`
- selected_unimplemented_runtime_effect_false_count: `0`
- selected_unimplemented_route_counts: `{}`
- selected_terminal_non_implement_runtime_effect_false_count: `5`
- selected_terminal_non_implement_route_counts: `{'ai_review_coverage_review': 1, 'positive_source_only_review': 1, 'source_dimension_rollup': 1, 'join_gap_enrichment': 1, 'source_quality_gap': 1}`
- selected_implement_now_existing_implementation_count: `0`
- selected_implement_now_existing_implementation_order_ids: `[]`
- selected_implement_now_new_runtime_effect_false_count: `0`
- selected_implement_now_new_runtime_effect_false_order_ids: `[]`
- repeat_unresolved_escalation_count: `0`
- repeat_unresolved_escalated_order_ids: `[]`
- repeat_unresolved_structural_blocker_count: `0`
- repeat_unresolved_structural_blocker_order_ids: `[]`
- root_cause_closure_status_counts: `{'handoff_closed_root_cause_open': 21, 'implementation_done': 10, 'root_cause_closed': 55}`
- implementation_done_count: `10`
- artifact_regeneration_required_count: `0`
- handoff_closed_root_cause_open_count: `21`
- root_cause_closed_count: `55`
- needs_followup_workorder_count: `0`
- root_cause_followup_contract_required_count: `21`
- root_cause_followup_contract_complete_count: `21`
- root_cause_followup_contract_missing_order_ids: `[]`
- root_cause_open_top: `[{'order_id': 'order_conversion_lane_bridge_contract_entry_wait6579_score66_69_recovery_gate_v1_2026_08_04', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:bridge_contract:bridge_contract:open', 'acceptance_test': 'runtime_apply_bridge emits explicit bridge blocker ledger or live_auto_apply_ready', 'next_repair_action': 'bridge_contract'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_437582bf', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_5db76271', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_66f70bfc', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_672cfe14', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_7868f88a', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_8d6ed15d', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_bbd448af', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_c06eb6b2', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}, {'order_id': 'order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_d8d36b81', 'status': 'handoff_closed_root_cause_open', 'source_report_type': 'conversion_lane', 'threshold_family': 'sim_to_real_conversion_lane', 'implementation_status': 'implemented', 'root_cause_signal': 'conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open', 'acceptance_test': 'source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass', 'next_repair_action': 'source_quality'}]`
- selected_terminal_non_implement_longstanding_count: `4`
- selected_terminal_non_implement_longstanding_order_ids: `['order_lifecycle_quiet_gap_ai_review_coverage_rollup', 'order_lifecycle_quiet_gap_positive_source_only_rollup', 'order_lifecycle_source_dimension_gap_rollup', 'order_lifecycle_source_dimension_join_gap_enrichment']`
- selected_longstanding_non_implement_disposition_counts: `{'keep_visible_by_design': 4}`
- selected_longstanding_non_implement_action_required_order_ids: `[]`
- non_selected_decision_counts: `{'attach_existing_family': 1, 'design_family_candidate': 3, 'defer_evidence': 1, 'reject': 1}`
- non_selected_longstanding_non_implement_disposition_counts: `{'implemented_with_provenance': 1, 'review_required': 4}`
- non_selected_longstanding_non_implement_action_required_order_ids: `[]`
- gemini_fresh: `False`
- claude_fresh: `True`
- swing_lifecycle_audit_available: `False`
- swing_pattern_lab_automation_available: `False`
- swing_pattern_lab_fresh: `None`
- pattern_lab_currentness_status: `pass`
- pattern_lab_currentness_fail_count: `0`
- pattern_lab_ai_review_status: `warning`
- pattern_lab_ai_review_workorder_count: `1`
- swing_threshold_ai_status: `None`
- daily_ev_available: `True`

## Codex 실행 지시

아래 order를 위에서부터 순서대로 처리한다. 각 order는 `판정 -> 근거 -> 다음 액션`으로 닫고, 코드 변경 시 관련 문서와 테스트를 함께 갱신한다.

필수 검증:

```bash
PYTHONPATH=. .venv/bin/pytest -q <관련 테스트 파일>
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project --print-backlog-only --limit 500
git diff --check
```

threshold/postclose 체인 영향 시 추가 검증:

```bash
bash -n deploy/run_threshold_cycle_preopen.sh deploy/run_threshold_cycle_calibration.sh deploy/run_threshold_cycle_postclose.sh
PYTHONPATH=. .venv/bin/pytest -q src/tests/test_daily_threshold_cycle_report.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_threshold_cycle_ev_report.py
```

## Implementation Orders

### 1. `order_entry_submit_drought_auto_resolution`

- title: Entry submit drought automatic resolution handoff
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `0`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: restore submitted coverage before evaluating EV edge
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`
- parity_contract: -
- next_postclose_metric: SUBMIT_DROUGHT_CRITICAL must produce a selected implement_now workorder and the next postclose LDM/runtime summary must show submit blocker attribution.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "artifact_regeneration_required": false, "broker_order_submit_allowed": false, "forbidden_uses": ["intraday_threshold_mutation", "broker_guard_bypass", "provider_route_change", "bot_restart_trigger", "telegram_pre_submit_buy_alert"], "implementation_type": "source_only_report_provenance_handoff", "ldm_quote_freshness_attribution_present": true, "observation_axis_status": {"BROKER_RECEIPT": "observed", "BUDGET_PASS_COLLAPSE": "observed", "ECONOMIC_PARTICIPATION": "observed", "LATENCY_PRE_SUBMIT": "observed", "SIM_REAL_AUTHORITY": "observed", "SOURCE_TAXONOMY_LEAKAGE": "no_current_signal", "UPSTREAM_GATE": "observed"}, "observation_breakdown": {"allowed_runtime_apply": false, "axes": {"BROKER_RECEIPT": {"evidence": {"latency_pass_unique": 39, "order_bundle_submitted_unique": 12, "submitted_to_budget_unique_pct": 12.9}, "next_repair_action": "join post-submit broker receipt and fill provenance when submitted samples exist", "observed_count": 27, "status": "observed"}, "BUDGET_PASS_COLLAPSE": {"evidence": {"ai_confirmed_unique": 209, "budget_pass_unique": 93, "budget_to_ai_unique_pct": 44.5}, "next_repair_action": "preserve budget pass collapse as source attribution before EV approval", "observed_count": 116, "status": "observed"}, "ECONOMIC_PARTICIPATION": {"evidence": {"allowed_runtime_apply": false, "bundle_count": 10, "by_venue": {"KRX": {"bundle_count": 10, "full_submitted_bundle_count": 0, "partial_residual_bundle_count": 1, "probe_only_bundle_count": 9, "requested_notional_krw": 1652518, "requested_qty": 234, "submitted_notional_krw": 215324, "submitted_notional_to_requested_notional_pct": 13.0, "submitted_qty": 38, "submitted_qty_to_requested_qty_pct": 16.2}}, "decision_authority": "submit_drought_attribution_only", "forbidden_uses": ["broker_order_submit", "intraday_threshold_mutation", "quantity_cap_release", "live_auto_promotion", "bot_restart_trigger"], "full_submitted_bundle_count": 0, "metric_role": "funnel_count", "observed_bundle_count": 10, "partial_residual_bundle_count": 1, "primary_decision_metric": "submitted_notional_to_requested_notional_pct", "probe_only_bundle_count": 9, "requested_notional_krw": 1652518, "requested_qty": 234, "rows": [{"attempt_key": "id:27158", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 103530, "requested_qty": 7, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "105840", "submitted_notional_krw": 14800, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27123", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 98940, "requested_qty": 6, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "484810", "submitted_notional_krw": 16540, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27214", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 99000, "requested_qty": 6, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "484810", "submitted_notional_krw": 16550, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27043", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 218790, "requested_qty": 13, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "402030", "submitted_notional_krw": 16840, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27041", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 157220, "requested_qty": 14, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "108860", "submitted_notional_krw": 11250, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27262", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 213300, "requested_qty": 18, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "452280", "submitted_notional_krw": 11890, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27329", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 200400, "requested_qty": 12, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "484810", "submitted_notional_krw": 16730, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27107", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 191880, "requested_qty": 13, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "194700", "submitted_notional_krw": 14820, "submitted_qty": 1, "venue_source_quality": "pass"}, {"attempt_key": "id:27180", "bundle_state": "partial_residual_submitted", "effective_venue": "KRX", "requested_notional_krw": 212858, "requested_qty": 142, "residual_submitted_qty": 28, "source_quality_valid": true, "stock_code": "459550", "submitted_notional_krw": 43504, "submitted_qty": 29, "venue_source_quality": "pass"}, {"attempt_key": "id:27028", "bundle_state": "probe_only", "effective_venue": "KRX", "requested_notional_krw": 156600, "requested_qty": 3, "residual_submitted_qty": 0, "source_quality_valid": true, "stock_code": "005090", "submitted_notional_krw": 52400, "submitted_qty": 1, "venue_source_quality": "pass"}], "runtime_effect": false, "sample_floor": "1_explicit_venue_probe_bundle", "source_quality_blocked_bundle_count": 0, "source_quality_gate": "explicit_conflict_free_venue_and_positive_requested_submitted_qty_price", "source_quality_valid_bundle_count": 10, "submitted_notional_krw": 215324, "submitted_notional_to_requested_notional_pct": 13.0, "submitted_qty": 38, "submitted_qty_to_requested_qty_pct": 16.2, "window_policy": "same_session_probe_bundle_lifecycle"}, "next_repair_action": "attribute probe-only and residual-submitted quantity/notional by explicit venue before interpreting submit conversion", "observed_count": 10, "status": "observed"}, "LATENCY_PRE_SUBMIT": {"evidence": {"latency_blocker_top": [{"count": 254, "label": "latency_block:latency_state_danger"}], "latency_root_cause_counts": {"quote_freshness_input_snapshot_noop": 186, "quote_stale": 126, "spread_microstructure_guard": 254, "spread_or_slippage_guard": 189}, "quote_freshness_attribution": {"decision_authority": "submit_drought_quote_freshness_attribution_only", "forbidden_uses": ["broker_order_submit", "adm_ldm_training_input", "general_threshold_ev_input", "live_auto_promotion"], "latency_pass_recovered_count": 6, "latency_pass_recovered_downstream_counts": {"budget_pass_no_submit_event": 1, "order_bundle_submitted": 1, "price_guard_or_revalidation": 4}, "latency_pass_recovered_downstream_stage_counts": {"budget_pass": 1, "order_bundle_submitted": 1, "pre_submit_entry_ai_authority_guard_block": 4}, "order_bundle_submitted_after_refresh_count": 1, "post_restart_window_policy": "event_provenance_only", "refresh_applied_count": 41, "refresh_attempted_count": 91, "refresh_block_subreason_counts": {"ws_snapshot_refresh_failed_input_snapshot_fresh": 186, "ws_snapshot_refresh_failed_stale": 18}, "refresh_subreason_counts": {"ws_snapshot_refresh_failed_input_snapshot_fresh": 186, "ws_snapshot_refresh_failed_stale": 18}, "runtime_effect": false, "still_latency_blocked_after_refresh_count": 68}, "unknown_latency_reason_count": 0, "unknown_latency_workorder_required": false}, "next_repair_action": "close unknown latency labels or route quote freshness gaps to LDM attribution", "observed_count": 254, "status": "observed"}, "SIM_REAL_AUTHORITY": {"evidence": {"actual_order_submitted_authority": "not_granted_by_report", "broker_order_submit_allowed": false}, "next_repair_action": "keep attribution source-only until explicit runtime approval artifact exists", "observed_count": 1, "status": "observed"}, "SOURCE_TAXONOMY_LEAKAGE": {"evidence": {"blocker_top": [{"count": 963, "label": "blocked_strength_momentum:below_window_buy_value"}, {"count": 876, "label": "blocked_overbought:-"}, {"count": 789, "label": "blocked_strength_momentum:insufficient_history"}, {"count": 375, "label": "blocked_liquidity:-"}, {"count": 319, "label": "blocked_vpw:-"}, {"count": 285, "label": "blocked_strength_momentum:below_strength_base"}, {"count": 254, "label": "latency_block:latency_state_danger"}, {"count": 218, "label": "blocked_zero_qty:-"}, {"count": 211, "label": "first_ai_wait:-"}, {"count": 152, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}], "taxonomy_leakage_labels": []}, "next_repair_action": "separate swing/source taxonomy from entry-submit blocker labels", "observed_count": 0, "status": "no_current_signal"}, "UPSTREAM_GATE": {"evidence": {"budget_to_ai_unique_pct": 44.5, "upstream_blocker_top": [{"count": 211, "label": "first_ai_wait:-"}, {"count": 152, "label": "blocked_ai_score:ai_score_50_buy_hold_override"}, {"count": 100, "label": "wait65_79_ev_candidate:score_65.0"}, {"count": 48, "label": "blocked_ai_score:score_11.0"}, {"count": 48, "label": "blocked_ai_score:score_65.0"}, {"count": 31, "label": "blocked_ai_score:score_0.0"}, {"count": 28, "label": "blocked_ai_score:score_13.0"}, {"count": 25, "label": "blocked_ai_score:score_14.0"}, {"count": 14, "label": "blocked_ai_score:score_17.0"}, {"count": 14, "label": "blocked_ai_score:score_19.0"}]}, "next_repair_action": "split upstream AI terminal and score gate reasons before threshold interpretation", "observed_count": 721, "status": "observed"}}, "axis_order": ["UPSTREAM_GATE", "BUDGET_PASS_COLLAPSE", "LATENCY_PRE_SUBMIT", "BROKER_RECEIPT", "ECONOMIC_PARTICIPATION", "SIM_REAL_AUTHORITY", "SOURCE_TAXONOMY_LEAKAGE"], "broker_order_submit_allowed": false, "decision_authority": "submit_drought_attribution_only", "forbidden_uses": ["broker_order_submit", "runtime_apply_candidate", "intraday_threshold_mutation", "provider_route_change", "bot_restart_trigger", "live_auto_promotion"], "runtime_effect": false}, "quote_freshness_attribution_inconsistent": false, "quote_freshness_latency_pass_recovered_count": 6, "quote_freshness_refresh_applied_count": 41, "quote_freshness_refresh_attempted_count": 91, "required_downstream": ["code_improvement_workorder", "lifecycle_decision_matrix.submit_bucket_attribution", "threshold_cycle_ev_report", "runtime_approval_summary", "postclose_verifier"], "root_cause_closure_status_hint": "root_cause_closed", "root_cause_counts": {"quote_freshness_input_snapshot_noop": 186, "quote_stale": 126, "spread_microstructure_guard": 254, "spread_or_slippage_guard": 189}, "root_cause_signal": "SUBMIT_DROUGHT_CRITICAL", "runtime_effect": false, "source_report_type": "buy_funnel_sentinel", "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 2. `order_conversion_lane_submit_drought_submit_drought_broker_receipt`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:BROKER_RECEIPT
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:BROKER_RECEIPT`, `blocker_class=submit_drought`, `conversion_impact_rank=1`, `next_repair_action=close_submit_drought_broker_receipt`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "BROKER_RECEIPT", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_broker_receipt", "root_cause_signal": "conversion_lane:submit_drought:BROKER_RECEIPT:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_broker_receipt", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_broker_receipt", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 3. `order_entry_broker_receipt_contract_gap_review`

- title: Entry broker receipt contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_submit_contract_verified; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`, `weak_contract_gap=broker_receipt_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "broker_receipt_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 13, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 54, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_entry_broker_receipt_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_broker_receipt_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 4. `order_entry_fill_quality_contract_gap_review`

- title: Entry fill quality contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_submit_contract_verified; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`, `weak_contract_gap=fill_quality_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "fill_quality_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 13, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 54, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_entry_fill_quality_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_fill_quality_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 5. `order_entry_post_submit_contract_gap_review`

- title: Entry post-submit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_submit_contract_verified; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`, `weak_contract_gap=post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 13, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 54, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_entry_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_post_submit_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 6. `order_entry_source_taxonomy_contract_gap_review`

- title: Entry source taxonomy contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_submit_contract_verified; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`, `weak_contract_gap=source_taxonomy_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`, `taxonomy_leakage_labels=[]`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "source_taxonomy_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 13, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 54, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_entry_source_taxonomy_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_source_taxonomy_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 7. `order_entry_telegram_post_submit_contract_gap_review`

- title: Entry Telegram post-submit contract gap review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_submit_contract_verified; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `buy_funnel_sentinel`
- lifecycle_stage: `entry_submit`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `-`
- confidence: `-`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `True`
- data_quality_effect: `True`
- tuning_axis_effect: `True`
- expected_ev_effect: none_direct_source_quality_only
- evidence: `ai_confirmed_unique=209`, `budget_pass_unique=93`, `latency_pass_unique=39`, `submitted_unique=12`, `submitted_to_ai_pct=5.7`, `submitted_to_budget_pct=12.9`, `blocker:blocked_strength_momentum:below_window_buy_value=963`, `blocker:blocked_overbought:-=876`, `blocker:blocked_strength_momentum:insufficient_history=789`, `upstream:first_ai_wait:-=211`, `upstream:blocked_ai_score:ai_score_50_buy_hold_override=152`, `upstream:wait65_79_ev_candidate:score_65.0=100`, `latency:latency_block:latency_state_danger=254`, `weak_contract_gap=telegram_post_submit_contract_gap`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: Entry post-submit weak contracts remain source-only workorders with runtime_effect=false and allowed_runtime_apply=false until explicit implementation and verification.
- files_likely_touched: `src/engine/buy_funnel_sentinel.py`, `src/engine/lifecycle_decision_matrix.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_buy_funnel_sentinel.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented_submit_contract_verified`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "downstream_consumer": "lifecycle_decision_matrix.submit_bucket_attribution", "gap_type": "telegram_post_submit_contract_gap", "implementation_type": "submit_contract_report_provenance_verified", "missing_broker_order_key_count": 0, "post_submit_provenance_join_resolution": "no_gap_broker_order_key_present_or_no_missing_rows", "real_submitted_row_count": 13, "runtime_effect": false, "sample_status": "ldm_submit_contract_verified", "source_report_type": "buy_funnel_sentinel", "submit_rows": 54, "taxonomy_leakage_labels": [], "weak_contract_matches": ["BROKER_RECEIPT", "BUDGET_PASS_COLLAPSE", "ECONOMIC_PARTICIPATION", "FILL_QUALITY", "LATENCY_PRE_SUBMIT", "PRICE_REVALIDATION", "SIM_REAL_AUTHORITY", "TELEGRAM_POST_SUBMIT_ONLY", "UPSTREAM_GATE"]}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_submit_contract_verified", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_entry_telegram_post_submit_contract_gap_review", "repeat_signature": "sig:buy_funnel_sentinel|runtime_instrumentation|entry_submit||lifecycle_decision_matrix_runtime|entry_telegram_post_submit_contract_gap_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_submit_contract_verified and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 8. `order_latency_canary_tag_완화_1축_canary_승인`

- title: latency canary tag 완화 1축 canary 승인
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `latency_canary_tag_완화_1축_canary_승인`
- confidence: `solo`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': 'tag_not_allowed blocker 감소로 진입 기회 확대', 'risk': 'bugfix-only 실표본 관찰 전 추가 완화는 해석 가능성 저하', 'required_sample': 'bugfix-only canary_applied 건수 50건 이상 (현재 19건)', 'metric': 'latency_canary_applied 증가, low_signal / tag_not_allowed 감소', 'apply_stage': 'canary_only_candidate_after_workorder'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "finding_id": "latency_canary_tag_완화_1축_canary_승인", "implementation_type": "pattern_lab_report_only_instrumentation", "runtime_effect": false, "source_report_type": "scalping_pattern_lab_automation", "target_subsystem": "runtime_instrumentation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_latency_canary_tag_완화_1축_canary_승인", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_canary_tag_완화_1축_canary_승인||latency_canary_tag_완화_1축_canary_승인", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 9. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_10_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_10`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 10. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_11_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_11`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 11. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_12_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_12`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 12. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_13_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9a776aeb`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_13`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 13. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_14_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_14`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 14. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_15_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_15`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 15. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_16_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9a776aeb`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_16`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 16. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_17_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_17`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 17. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_18_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_18`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 18. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_19_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_042316e2`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:44584d6a76
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_19`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:44584d6a76`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 19. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_1_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_1`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 20. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_20_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_da44f074`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:01014e4cdc
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_20`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:01014e4cdc`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 21. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_2_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_2`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 22. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_3_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_0166b02a`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_3`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:34865a272b`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 23. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_4_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9a776aeb`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_4`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 24. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_5_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_5`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 25. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_6_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_9a776aeb`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_6`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:b528e0c876`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 26. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_7_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_7`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 27. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_8_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2ad7fdfe`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_8`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:53da8da968`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_submit', 'missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 28. `order_lifecycle_flow_bucket_lifecycle_flow_bucket_incomplete_9_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_entry_spot_score_2dd03a07`

- title: LDM lifecycle flow bucket follow-up: lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_lifecycle_flow_bucket_attribution`
- lifecycle_stage: `lifecycle_flow`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `join_gap_resolution`
- confidence: `daily_ldm_source`
- priority: `1`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Prevent entry-only EV from being interpreted as full lifecycle EV by keeping incomplete parent flow bundles visible as source-quality evidence.
- evidence: `workorder_id=lifecycle_flow_bucket_incomplete_9`, `lifecycle_flow_bucket_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_sca:c69a7be5bd`, `reason=incomplete_lifecycle_flow`, `join_gap_reasons=['missing_holding', 'missing_exit']`, `required_producer_consumer_candidates=['entry producer', 'submit observation', 'holding flow', 'exit/post-sell feedback', 'bridge key normalizer']`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_lifecycle_flow_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_flow bucket counts, complete-flow counts, runtime candidates, and workorders must be visible in threshold EV, runtime summary, control tower, and verifier.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/lifecycle_bucket_discovery.py`, `src/engine/runtime_approval_summary.py`, `src/engine/runtime_apply_bridge.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_lifecycle_bucket_discovery.py src/tests/test_runtime_apply_bridge.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if lifecycle-flow parent bucket output is dropped`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "repeat_signature": "sig:lifecycle_decision_matrix_lifecycle_flow_bucket_attribution|lifecycle_decision_matrix|lifecycle_flow|join_gap_resolution|lifecycle_decision_matrix_runtime|ldm_lifecycle_flow_bucket_follow_up_lifecycle_flow_combo_lifecycle_flow_entry_en", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 29. `order_conversion_lane_submit_drought_submit_drought_budget_pass_collapse`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:BUDGET_PASS_COLLAPSE
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:BUDGET_PASS_COLLAPSE`, `blocker_class=submit_drought`, `conversion_impact_rank=2`, `next_repair_action=close_submit_drought_budget_pass_collapse`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "BUDGET_PASS_COLLAPSE", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_budget_pass_collapse", "root_cause_signal": "conversion_lane:submit_drought:BUDGET_PASS_COLLAPSE:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_budget_pass_collapse", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_budget_pass_coll", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 30. `order_latency_guard_miss_ev_recovery`

- title: latency guard miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/provenance contract is already implemented; keep as report source for the existing family
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `dynamic_entry_price_resolver`
- threshold_family: `dynamic_entry_price_resolver`
- improvement_type: `latency_guard_miss_ev_recovery`
- confidence: `solo`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 4146, 'block_ratio': 92.1, 'days': 27}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/sniper_performance_tuning_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "finding_id": "latency_guard_miss_ev_recovery", "implementation_type": "pattern_lab_report_only_instrumentation", "runtime_effect": false, "source_report_type": "scalping_pattern_lab_automation", "target_subsystem": "runtime_instrumentation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_latency_guard_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|runtime_instrumentation||latency_guard_miss_ev_recovery||latency_guard_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose calibration consumes the implemented report/provenance fields; no runtime mutation.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 31. `order_lifecycle_entry_bucket_exit_rule_exit_unknown`

- title: LDM entry bucket attribution follow-up: exit_rule=exit_unknown
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `runtime_instrumentation`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_5`, `bucket_type=exit_rule`, `bucket_key=exit_unknown`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "entry_label_not_applicable", "source_field_coverage": {"exit_rule": {"coverage_rate": 0.0, "present_count": 0, "sample_count": 912, "source_fields": ["labels.exit_rule"]}}, "unknown_dimension_counts": {"exit_rule": 1}, "unknown_reason_counts": {"entry_label_not_applicable": 1}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_entry_bucket_exit_rule_exit_unknown", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|runtime_instrumentation|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_exit_rule_exit_unknown", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 32. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_73281913`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_1`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_neg070_neg010", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 33. `order_lifecycle_exit_bucket_combo_exit_result_source_scalp_sim_partial_sell_order_assumed_filled_rule_scalp_sim_panic_823fe278`

- title: LDM exit bucket source-quality follow-up: combo_exit_result=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_2`, `bucket_type=combo_exit_result`, `bucket_key=source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "source=scalp_sim_partial_sell_order_assumed_filled|rule=scalp_sim_panic_lifecycle_partial_exit|outcome=outcome_not_applicable_partial_exit|profit=profit_lt_neg070", "bucket_type": "combo_exit_result", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 34. `order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit`

- title: LDM exit bucket source-quality follow-up: exit_outcome=outcome_not_applicable_partial_exit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_3`, `bucket_type=exit_outcome`, `bucket_key=outcome_not_applicable_partial_exit`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "outcome_not_applicable_partial_exit", "bucket_type": "exit_outcome", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_exit_bucket_exit_outcome_outcome_not_applicable_partial_exit", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_outcome_outcome_not_applicable_par", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 35. `order_lifecycle_exit_bucket_exit_rule_scalp_sim_panic_lifecycle_partial_exit`

- title: LDM exit bucket source-quality follow-up: exit_rule=scalp_sim_panic_lifecycle_partial_exit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_4`, `bucket_type=exit_rule`, `bucket_key=scalp_sim_panic_lifecycle_partial_exit`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_panic_lifecycle_partial_exit", "bucket_type": "exit_rule", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_exit_bucket_exit_rule_scalp_sim_panic_lifecycle_partial_exit", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_rule_scalp_sim_panic_lifecycle_par", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 36. `order_lifecycle_exit_bucket_exit_source_stage_scalp_sim_partial_sell_order_assumed_filled`

- title: LDM exit bucket source-quality follow-up: exit_source_stage=scalp_sim_partial_sell_order_assumed_filled
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_5`, `bucket_type=exit_source_stage`, `bucket_key=scalp_sim_partial_sell_order_assumed_filled`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "scalp_sim_partial_sell_order_assumed_filled", "bucket_type": "exit_source_stage", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_exit_bucket_exit_source_stage_scalp_sim_partial_sell_order_assumed_filled", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_exit_source_stage_scalp_sim_partial_sel", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 37. `order_lifecycle_exit_bucket_profit_band_profit_lt_neg070`

- title: LDM exit bucket source-quality follow-up: profit_band=profit_lt_neg070
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_7`, `bucket_type=profit_band`, `bucket_key=profit_lt_neg070`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_lt_neg070", "bucket_type": "profit_band", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_exit_bucket_profit_band_profit_lt_neg070", "repeat_signature": "sig:lifecycle_decision_matrix_exit_bucket_attribution|lifecycle_decision_matrix|exit|exit_bucket_source_quality_child_evidence|lifecycle_decision_matrix_runtime|ldm_exit_bucket_source_quality_follow_up_profit_band_profit_lt_neg070", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 38. `order_lifecycle_exit_bucket_profit_band_profit_neg070_neg010`

- title: LDM exit bucket source-quality follow-up: profit_band=profit_neg070_neg010
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_exit_bucket_attribution`
- lifecycle_stage: `exit`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `exit_bucket_source_quality_child_evidence`
- confidence: `daily_ldm_source`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep exit stage buckets visible as child evidence while parent lifecycle flow owns promotion EV.
- evidence: `workorder_id=exit_bucket_source_quality_6`, `bucket_type=profit_band`, `bucket_key=profit_neg070_neg010`, `reason=exit_stage_bucket_needs_source_quality_or_lifecycle_flow_confirmation`, `recommended_route=candidate_tighten_or_exclude`, `runtime_effect=false`, `allowed_runtime_apply=false`, `stage_only_live_promotion_forbidden=true`
- parity_contract: -
- next_postclose_metric: exit_bucket_attribution bucket/workorder counts, identity join rate, and complete lifecycle flow count remain visible in downstream reports.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"ai_inference_proposal": {"allowed_runtime_apply": false, "bucket_key": "profit_neg070_neg010", "bucket_type": "profit_band", "decision_point": "exit_bucket_classification", "deterministic_decision": "candidate_tighten_or_exclude", "model": "gpt-5.4-mini", "proposal_type": "ai_inference_parallel_review_required", "reason": "parallel_ai_inference_for_deterministic_bucket_decision", "reasoning_effort": "medium", "review_contract": {"ai_has_promotion_authority": false, "model": "gpt-5.4", "reasoning_effort": "low", "runtime_effect": false}, "runtime_effect": false, "source_quality_gate": "pass"}, "recommended_resolution": "none", "source_field_coverage": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 39. `order_one_share_threshold_strength_momentum_vpw_entry_hook_review`

- title: one-share threshold opportunity entry hook review: strength_momentum_vpw
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `one_share_threshold_opportunity`
- lifecycle_stage: `entry`
- target_subsystem: `entry_strength_momentum_history_recheck`
- route: `existing_family`
- mapped_family: `entry_strength_momentum_recheck`
- threshold_family: `entry_strength_momentum_recheck`
- improvement_type: `source_only_entry_hook_workorder`
- confidence: `rolling_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use one-share forced-entry post-sell outcomes to improve bounded entry hook selection without treating one-share PnL as standalone real-order approval evidence.
- evidence: `threshold_group=strength_momentum_vpw`, `sample=174`, `valid_profit_sample=174`, `profitable_count=116`, `loss_or_flat_count=58`, `equal_weight_avg_profit_pct=0.014598`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/one_share_threshold_opportunity.py`, `src/engine/scalping/entry_opportunity_recheck.py`, `src/engine/sniper_state_handlers.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_one_share_threshold_opportunity.py src/tests/test_entry_opportunity_recheck.py src/tests/test_build_code_improvement_workorder.py`, `source-only audit must not mutate intraday runtime thresholds, broker/order guards, provider route, bot state, quantity, or caps`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_only_threshold_opportunity_audit", "equal_weight_avg_profit_pct": 0.014598, "forbidden_uses": ["runtime_threshold_mutation", "buy_score_threshold_relaxation_without_preopen_apply", "stale_submit_bypass", "broker_guard_bypass", "order_guard_relaxation", "provider_route_change", "bot_restart", "forced_one_share_success_counting", "real_execution_quality_approval"], "implementation_type": "one_share_threshold_opportunity_audit", "implemented_scope": "source-only threshold group audit and code-improvement order provenance", "mapped_family": "entry_strength_momentum_recheck", "primary_decision_metric": "equal_weight_avg_profit_pct", "requires_separate_runtime_apply_candidate": true, "runtime_effect": false, "runtime_mutation_allowed": false, "sample": 174, "source_quality_gate": "record_id_joined_forced_one_share_event_to_post_sell_outcome", "threshold_group": "strength_momentum_vpw", "valid_profit_sample": 174}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_one_share_threshold_strength_momentum_vpw_entry_hook_review", "repeat_signature": "sig:one_share_threshold_opportunity|entry_strength_momentum_history_recheck|entry|source_only_entry_hook_workorder|entry_strength_momentum_recheck|one_share_threshold_opportunity_entry_hook_review_strength_momentum_vpw", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 40. `order_rising_missed_classifier_prior_feedback_bridge`

- title: rising missed cumulative classifier prior bridge
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- route: `existing_family`
- mapped_family: `rising_missed_classifier_prior_feedback_bridge`
- threshold_family: `rising_missed_classifier_prior_feedback_bridge`
- improvement_type: `source_only_classifier_prior_workorder`
- confidence: `cumulative_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Feed cumulative ADM/LDM prior recommendations back into the rising-missed scout loop as source-only classifier evidence.
- evidence: `prior_count=126`, `recommendation_counts={"hold_sample": 90, "loss_filter": 30, "positive_prior": 5, "source_quality_blocked": 1}`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_classifier_prior.py`, `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/scalping/rising_missed_one_share_entry.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_classifier_prior.py src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `prior bridge remains source-only and cannot mutate one-share allow/block, runtime thresholds, broker/order guards, provider route, or bot state`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_classifier_prior_no_runtime_mutation", "implementation_type": "rising_missed_classifier_prior_feedback_bridge", "prior_count": 126, "recommendation_counts": {"hold_sample": 90, "loss_filter": 30, "positive_prior": 5, "source_quality_blocked": 1}, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_classifier_prior_feedback_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|rising_missed_entry_classifier|entry|source_only_classifier_prior_workorder|rising_missed_classifier_prior_feedback_bridge|rising_missed_cumulative_classifier_prior_bridge", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 41. `order_rising_missed_scout_loss_filter`

- title: rising missed scout loss filter before any expansion
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_risk_filter`
- route: `existing_family`
- mapped_family: `rising_missed_scout_loss_filter`
- threshold_family: `rising_missed_scout_loss_filter`
- improvement_type: `source_only_operational_workorder`
- confidence: `same_day_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate profitable forced-scout examples from stop/soft-stop losers before any normal-entry or scout-expansion proposal.
- evidence: `loser_count=5`, `loser_avg_profit_rate=-2.082`, `loser_avg_peak_profit=0.46`, `shared_source_signature_count=1`, `losers_also_had_latency_pass=True`, `losers_also_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `loss filter is source-only and does not relax stops or broker/order guards`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_loss_filter_source_split", "joined_post_sell_loser_count": 5, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_rising_missed_scout_loss_filter", "repeat_signature": "sig:rising_missed_scout_workorder|entry_risk_filter|entry|source_only_operational_workorder|rising_missed_scout_loss_filter|rising_missed_scout_loss_filter_before_any_expansion", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 42. `order_rising_missed_scout_post_sell_bridge`

- title: rising missed scout post-sell bridge for normal-entry recheck
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `entry`
- target_subsystem: `entry_freshness`
- route: `existing_family`
- mapped_family: `rising_missed_scout_post_sell_bridge`
- threshold_family: `rising_missed_scout_post_sell_bridge`
- improvement_type: `source_only_operational_workorder`
- confidence: `same_day_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use forced-scout post-sell MFE/profit and holding-quality evidence to request a bounded normal-entry recheck workorder; do not count forced scouts as normal BUY success.
- evidence: `winner_count=8`, `loser_count=5`, `winner_avg_profit_rate=1.1175`, `shared_source_signature_count=1`, `runner_review_candidate_count=4`, `current_missed_count=0`, `current_missed_eligible_count=0`, `all_winner_rows_had_latency_pass=True`, `all_winner_rows_had_order_bundle_submitted=True`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/build_code_improvement_workorder.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `forced scout remains excluded from normal BUY/submit/fill success counts`, `runtime_effect remains false until a separate approved runtime family exists`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_operational_workorder", "implementation_type": "forced_scout_post_sell_source_bridge", "joined_post_sell_loser_count": 5, "joined_post_sell_winner_count": 8, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 6, "repeat_key": "order_rising_missed_scout_post_sell_bridge", "repeat_signature": "sig:rising_missed_scout_workorder|entry_freshness|entry|source_only_operational_workorder|rising_missed_scout_post_sell_bridge|rising_missed_scout_post_sell_bridge_for_normal_entry_recheck", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 43. `order_rising_missed_scout_take_profit_capture_review`

- title: rising missed scout take-profit capture review
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_scout_workorder`
- lifecycle_stage: `holding_exit`
- target_subsystem: `take_profit_and_trailing_capture`
- route: `existing_family`
- mapped_family: `rising_missed_scout_take_profit_capture_review`
- threshold_family: `rising_missed_scout_take_profit_capture_review`
- improvement_type: `source_only_exit_capture_workorder`
- confidence: `same_day_source_only`
- priority: `2`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Separate profitable forced-scout rows with measurable peak-profit giveback into a runner/partial-TP review cohort before any take-profit or trailing policy proposal.
- evidence: `winner_count=8`, `evaluated_capture_count=8`, `avg_peak_profit=1.6987`, `avg_profit_rate=1.1175`, `avg_giveback_pct=0.5813`, `runner_review_candidate_count=4`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/monitoring/rising_missed_scout_workorder.py`, `src/engine/holding_exit_observation_report.py`, `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_rising_missed_scout_workorder.py src/tests/test_build_code_improvement_workorder.py`, `take-profit capture review remains source-only and cannot widen TP/trailing or force holding extension`
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "source_only_take_profit_expansion_review", "implementation_type": "forced_scout_take_profit_capture_source_split", "root_cause_closure_status_hint": "implementation_done", "runner_review_candidate_count": 4, "runtime_effect": false, "winner_count": 8}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_rising_missed_scout_take_profit_capture_review", "repeat_signature": "sig:rising_missed_scout_workorder|take_profit_and_trailing_capture|holding_exit|source_only_exit_capture_workorder|rising_missed_scout_take_profit_capture_review|rising_missed_scout_take_profit_capture_review", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 44. `order_ai_threshold_miss_ev_recovery`

- title: AI threshold miss EV recovery
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_funnel`
- route: `existing_family`
- mapped_family: `score65_74_recovery_probe`
- threshold_family: `score65_74_recovery_probe`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'total_blocked': 24182, 'block_ratio': 98.6, 'days': 27}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_missed_entry_counterfactual.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_existing_family_source_metric", "implemented_scope": "score65_74_recovery_probe_source_metric_provenance", "runtime_effect": false, "source_contract": "scalping_ai_threshold_miss_source_metric_v1", "source_fields": ["total_blocked", "block_ratio", "days"], "source_metric_snapshot": {"block_ratio": 98.6, "days": 27, "mapped_family": "score65_74_recovery_probe", "total_blocked": 24182}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_ai_threshold_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_funnel||threshold_family_input||ai_threshold_miss_ev_recovery", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 45. `order_conversion_lane_submit_drought_submit_drought_latency_pre_submit`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:LATENCY_PRE_SUBMIT
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:LATENCY_PRE_SUBMIT`, `blocker_class=submit_drought`, `conversion_impact_rank=3`, `next_repair_action=close_submit_drought_latency_pre_submit_quote_freshness`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "LATENCY_PRE_SUBMIT", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_latency_pre_submit_quote_freshness", "root_cause_signal": "conversion_lane:submit_drought:LATENCY_PRE_SUBMIT:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_latency_pre_submit", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_latency_pre_subm", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 46. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_entry_6d966faa56`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:entry:source_key_entry
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:entry:source_key_entry`, `source_bucket_id=source_contract:source_added:entry:6d966faa56`, `canonical_bucket=source_contract:source_added:entry`, `legacy_raw_bucket_key=entry`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=hybrid`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 47. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_lifecycle_ai_context_attribution_8b12f01b14`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:lifecycle_ai_context_attribution:source_key_lifecycle_ai_context_attribution`, `source_bucket_id=source_contract:source_added:lifecycle_ai_context_attribution:8b12f01b14`, `canonical_bucket=source_contract:source_added:lifecycle_ai_context_attribution`, `legacy_raw_bucket_key=lifecycle_ai_context_attribution`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=hybrid`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=existing_bucket_refinement`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 48. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scale_in_attribution_792528d29e`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scale_in_attribution:source_key_scale_in_attribution`, `source_bucket_id=source_contract:source_added:scale_in_attribution:792528d29e`, `canonical_bucket=source_contract:source_added:scale_in_attribution`, `legacy_raw_bucket_key=scale_in_attribution`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 49. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_holding_1fe719177c`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scalp_sim_holding:source_key_scalp_sim_holding`, `source_bucket_id=source_contract:source_added:scalp_sim_holding:1fe719177c`, `canonical_bucket=source_contract:source_added:scalp_sim_holding`, `legacy_raw_bucket_key=scalp_sim_holding`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 50. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_overnight_bbc5c8073f`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scalp_sim_overnight:source_key_scalp_sim_overnight`, `source_bucket_id=source_contract:source_added:scalp_sim_overnight:bbc5c8073f`, `canonical_bucket=source_contract:source_added:scalp_sim_overnight`, `legacy_raw_bucket_key=scalp_sim_overnight`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 51. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_panic_2d758895e8`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scalp_sim_panic:source_key_scalp_sim_panic`, `source_bucket_id=source_contract:source_added:scalp_sim_panic:2d758895e8`, `canonical_bucket=source_contract:source_added:scalp_sim_panic`, `legacy_raw_bucket_key=scalp_sim_panic`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 52. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_scale_in_266afa66b7`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scalp_sim_scale_in:source_key_scalp_sim_scale_in`, `source_bucket_id=source_contract:source_added:scalp_sim_scale_in:266afa66b7`, `canonical_bucket=source_contract:source_added:scalp_sim_scale_in`, `legacy_raw_bucket_key=scalp_sim_scale_in`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 53. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_scalp_sim_submit_4337b300b2`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:scalp_sim_submit:source_key_scalp_sim_submit`, `source_bucket_id=source_contract:source_added:scalp_sim_submit:4337b300b2`, `canonical_bucket=source_contract:source_added:scalp_sim_submit`, `legacy_raw_bucket_key=scalp_sim_submit`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 54. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_sim_post_sell_db99eef989`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:sim_post_sell:source_key_sim_post_sell
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:sim_post_sell:source_key_sim_post_sell`, `source_bucket_id=source_contract:source_added:sim_post_sell:db99eef989`, `canonical_bucket=source_contract:source_added:sim_post_sell`, `legacy_raw_bucket_key=sim_post_sell`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 55. `order_lifecycle_bucket_discovery_source_contract_source_contract_source_added_wait6579_c8aa00f461`

- title: Lifecycle bucket discovery follow-up: source_contract:source_added:wait6579:source_key_wait6579
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_source_quality_contract_available; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_bucket_discovery`
- lifecycle_stage: `source_contract`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `existing_family`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `bucket_classifier_hook_or_taxonomy_gap`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close lifecycle bucket discovery hook/taxonomy gaps so future postclose discovery can auto-classify and auto-apply without operator memory.
- evidence: `bucket_id=source_contract:source_added:wait6579:source_key_wait6579`, `source_bucket_id=source_contract:source_added:wait6579:c8aa00f461`, `canonical_bucket=source_contract:source_added:wait6579`, `legacy_raw_bucket_key=wait6579`, `bucket_alias_version=lifecycle_bucket_alias_v1`, `dimension_set_version=lifecycle_dimension_set_v1`, `bucket_absorption_reason=keep_existing_bucket`, `ai_tier2_taxonomy_decision=keep_bucket`, `ai_tier2_selected_source=deterministic`, `source_bucket_kind=source_only_observation`, `stage=source_contract`, `classification_state=new_bucket_candidate`, `bucket_relation=new_bucket_candidate`, `recommended_action=update_source_contract_or_taxonomy`, `recommended_resolution=update_source_contract_or_taxonomy`, `source_dimension_gap=`, `missing_dimension_keys=[]`, `missing_lifecycle_flow_stage_keys=[]`, `unknown_reason_counts={}`, `source_quality_adjusted_ev_pct=None`, `runtime_effect=false_until_patch_review_passes`, `allowed_runtime_apply=false_until_contract_hook_tests_pass`
- parity_contract: -
- next_postclose_metric: lifecycle_bucket_discovery should classify this bucket as sim_auto_approved or live_auto_apply_ready, or keep it source-only with an explicit blocker.
- files_likely_touched: `src/engine/lifecycle_bucket_discovery.py`, `src/engine/threshold_cycle_preopen_apply.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_bucket_discovery.py src/tests/test_threshold_cycle_preopen_apply.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier reports automation_handoff_gap if surfaced discovery candidates are dropped`
- implementation_status: `implemented_source_quality_contract_available`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"actual_order_submitted": false, "ai_tier2_taxonomy_decision": "keep_bucket", "allowed_runtime_apply": false, "broker_order_forbidden": true, "decision_authority": "source_contract_drift_detection", "evidence_grade": "source_only", "implementation_type": "lifecycle_source_contract_drift_source_only_provenance", "root_cause_closure_status_hint": "root_cause_closed", "runtime_effect": false, "source_bucket_kind": "source_only_observation", "source_contract_change_count": 10, "source_contract_status": "warning", "transition_target": "source_only_keep_collecting"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_source_quality_contract_available and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 56. `order_lifecycle_quiet_gap_ai_review_coverage_rollup`

- title: Lifecycle quiet gap AI review coverage review
- decision: `attach_existing_family`
- decision_reason: quiet gap rollup is visibility evidence for parent conflict/source-only/AI coverage review; it does not authorize a runtime patch by itself
- source_report_type: `lifecycle_bucket_discovery_quiet_gap_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `ai_review_coverage_review`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `quiet_gap_rollup_evidence`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep quiet source-quality gaps visible without treating every rollup as an immediate code patch requirement.
- evidence: `quiet_gap_count=327`, `rollup_required_count=327`, `sim_live_connected_quiet_gap_count=0`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 326, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 3, 'reviewed_candidate_count': 3, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "ai_review_coverage_review", "repeat_count": 7, "repeat_key": "order_lifecycle_quiet_gap_ai_review_coverage_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_ai_review_coverage_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 57. `order_lifecycle_quiet_gap_positive_source_only_rollup`

- title: Lifecycle quiet gap positive source-only review
- decision: `attach_existing_family`
- decision_reason: quiet gap rollup is visibility evidence for parent conflict/source-only/AI coverage review; it does not authorize a runtime patch by itself
- source_report_type: `lifecycle_bucket_discovery_quiet_gap_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `positive_source_only_review`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `quiet_gap_rollup_evidence`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep quiet source-quality gaps visible without treating every rollup as an immediate code patch requirement.
- evidence: `quiet_gap_count=327`, `rollup_required_count=327`, `sim_live_connected_quiet_gap_count=0`, `quiet_gap_type_counts={'positive_source_only_keep_collecting': 326, 'ai_review_parsed_low_coverage': 1}`, `ai_review_coverage={'status': 'parsed', 'shard_count': 5, 'parsed_shard_count': 3, 'reviewed_candidate_count': 3, 'low_coverage': True}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: quiet_gap_summary rollup counts remain visible until explicitly resolved.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "positive_source_only_review", "repeat_count": 7, "repeat_key": "order_lifecycle_quiet_gap_positive_source_only_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_quiet_gap_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|quiet_gap_rollup_evidence|lifecycle_bucket_discovery|lifecycle_quiet_gap_positive_source_only_review", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep quiet_gap_summary visible until the gap is implemented, covered by parent policy, deferred for more sample, or explicitly rejected.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 58. `order_lifecycle_source_dimension_gap_rollup`

- title: None
- decision: `attach_existing_family`
- decision_reason: source-dimension gap rollup is visibility evidence; actionable emit/backfill gaps are tracked by dedicated lifecycle_bucket_discovery implement_now orders
- source_report_type: `lifecycle_bucket_discovery_source_dimension_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `source_dimension_rollup`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_gap_rollup_evidence`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep repeated source-dimension gaps visible without treating not-applicable or absorbed dimensions as immediate code defects.
- evidence: `rollup_only_gap_count=47`, `unknown_source_dimensions=2`, `recommended_resolution_counts={'explicit_lifecycle_flow_source_only_blocker': 45, 'entry_label_not_applicable': 1, 'join_labels_before_bucket_decision': 1}`, `missing_dimension_key_counts={'entry': 10, 'exit': 86, 'holding': 90, 'submit': 66}`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary rollup/actionable counts remain visible.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "source_dimension_rollup", "repeat_count": 5, "repeat_key": "order_lifecycle_source_dimension_gap_rollup", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_gap_rollup_evidence|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 59. `order_lifecycle_source_dimension_join_gap_enrichment`

- title: None
- decision: `attach_existing_family`
- decision_reason: source-dimension gap rollup is visibility evidence; actionable emit/backfill gaps are tracked by dedicated lifecycle_bucket_discovery implement_now orders
- source_report_type: `lifecycle_bucket_discovery_source_dimension_rollup`
- lifecycle_stage: `multi_stage`
- target_subsystem: `lifecycle_bucket_discovery_taxonomy_provenance`
- route: `join_gap_enrichment`
- mapped_family: `lifecycle_bucket_discovery`
- threshold_family: `lifecycle_bucket_discovery`
- improvement_type: `source_dimension_join_gap_enrichment`
- confidence: `postclose_discovery_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep LDM bucket label/join gaps visible as source-quality provenance before any bucket decision or runtime apply interpretation.
- evidence: `join_gap_candidate_count=1`, `join_gap_stage_counts={'entry': 1}`, `join_gap_bucket_type_counts={'strength_bucket': 1}`, `join_gap_recommended_resolution_counts={'join_labels_before_bucket_decision': 1}`, `join_gap_missing_dimension_key_counts={}`, `recommended_next_action=enrich_bucket_label_or_join_key_before_bucket_decision`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: source_dimension_gap_summary.join_gap_enrichment candidate_count is tracked until explicitly closed.
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "terminal_existing_family_evidence", "previous_route": "join_gap_enrichment", "repeat_count": 5, "repeat_key": "order_lifecycle_source_dimension_join_gap_enrichment", "repeat_signature": "sig:lifecycle_bucket_discovery_source_dimension_rollup|lifecycle_bucket_discovery_taxonomy_provenance|multi_stage|source_dimension_join_gap_enrichment|lifecycle_bucket_discovery|unknown", "review_disposition": "keep_visible_by_design"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose checklist/workorder should keep source_dimension_gap_summary visible until actionable gaps are resolved or explicitly marked not applicable.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 60. `order_rising_missed_classifier_prior_bridge`

- title: Attach cumulative ADM/LDM prior lookup to rising-missed classifier reports
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `rising_missed_classifier_prior`
- lifecycle_stage: `entry`
- target_subsystem: `rising_missed_entry_classifier`
- route: `existing_family`
- mapped_family: `rising_missed_classifier_prior_bridge`
- threshold_family: `rising_missed_classifier_prior_bridge`
- improvement_type: `-`
- confidence: `-`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: None
- evidence: `prior_count=126`, `positive_prior_count=5`, `source_quality_blocked_count=1`, `bounded_probe_exploration_candidate_count=3`, `raw_adverse_first_is_standalone_veto=false`, `runtime_effect=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: -
- acceptance_tests: -
- implementation_status: `implemented`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "broker_order_forbidden": true, "implementation_type": "rising_missed_classifier_prior_source_only", "requires_separate_runtime_apply_candidate": true, "root_cause_closure_status_hint": "implementation_done", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_rising_missed_classifier_prior_bridge", "repeat_signature": "sig:rising_missed_classifier_prior|rising_missed_entry_classifier|entry||rising_missed_classifier_prior_bridge|attach_cumulative_adm_ldm_prior_lookup_to_rising_missed_classifier_reports", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 61. `order_scale_in_split_order_plan_contract_gap`

- title: scale-in split order plan report/source-quality contract gap
- decision: `attach_existing_family`
- decision_reason: finding maps to an existing threshold family and should strengthen source metrics/provenance
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `scale_in`
- target_subsystem: `scale_in_split_order_plan`
- route: `source_quality_gap`
- mapped_family: `scale_in_split_order_plan`
- threshold_family: `scale_in_split_order_plan`
- improvement_type: `base_price_reconstruction_gap,price_observation_join_gap`
- confidence: `postclose_threshold_ev_source`
- priority: `3`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Close report/source-quality/runtime-hook gaps so threshold-cycle can pass an AVG_DOWN qty-preserving split policy to next PREOPEN.
- evidence: `status=pass`, `schema_version=scale_in_split_order_plan_v1`, `candidate_grid_count=6`, `recommended_policy_candidate_count=3`, `counterfactual_selected_count=3`, `price_observation_join_gap_count=2`, `base_price_reconstruction_gap_count=2`
- parity_contract: -
- next_postclose_metric: scale_in_split_order_plan should provide valid schema, source-quality pass/exclusion, candidate_grid, post-submit price observation joins, and recommended_policy.
- files_likely_touched: `src/engine/scalping/scale_in_split_order_plan.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_scale_in_split_order_plan.py src/tests/test_daily_threshold_cycle_report.py`, `Runtime hook must preserve total scale-in qty and not bypass broker guards.`
- implementation_status: `terminal_existing_family_evidence`
- root_cause_closure_status: `-`
- implementation_provenance: `-`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: After implementation, intraday/postclose calibration should include the updated family input.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 62. `order_conversion_lane_submit_drought_submit_drought_sim_real_authority`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:SIM_REAL_AUTHORITY
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `4`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:SIM_REAL_AUTHORITY`, `blocker_class=submit_drought`, `conversion_impact_rank=4`, `next_repair_action=close_submit_drought_sim_real_authority`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "SIM_REAL_AUTHORITY", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_sim_real_authority", "root_cause_signal": "conversion_lane:submit_drought:SIM_REAL_AUTHORITY:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_sim_real_authority", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_sim_real_authori", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 63. `order_conversion_lane_submit_drought_submit_drought_source_taxonomy_leakage`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:SOURCE_TAXONOMY_LEAKAGE
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:SOURCE_TAXONOMY_LEAKAGE`, `blocker_class=submit_drought`, `conversion_impact_rank=5`, `next_repair_action=close_submit_drought_source_taxonomy_leakage`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "SOURCE_TAXONOMY_LEAKAGE", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_source_taxonomy_leakage", "root_cause_signal": "conversion_lane:submit_drought:SOURCE_TAXONOMY_LEAKAGE:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_source_taxonomy_leakage", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_source_taxonomy_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 64. `order_lifecycle_entry_bucket_chosen_action_no_buy_ai`

- title: LDM entry bucket attribution follow-up: chosen_action=NO_BUY_AI
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_2`, `bucket_type=chosen_action`, `bucket_key=NO_BUY_AI`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 65. `order_lifecycle_entry_bucket_chosen_action_skip_pre_submit_safety`

- title: LDM entry bucket attribution follow-up: chosen_action=SKIP_PRE_SUBMIT_SAFETY
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_1`, `bucket_type=chosen_action`, `bucket_key=SKIP_PRE_SUBMIT_SAFETY`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 4, "repeat_key": "order_lifecycle_entry_bucket_chosen_action_skip_pre_submit_safety", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_chosen_action_skip_pre_submit_safety", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 66. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_stal_3da5a749`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_3`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_0900_1000`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_lt60_source_", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_lt60_source_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 67. `order_lifecycle_entry_bucket_combo_entry_spot_score_score_lt60_source_scalp_entry_action_decision_snapshot_stale_stal_de8ea321`

- title: LDM entry bucket attribution follow-up: combo_entry_spot=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_4`, `bucket_type=combo_entry_spot`, `bucket_key=score=score_lt60|source=scalp_entry_action_decision_snapshot|stale=stale_not_available|liquidity=liquidity_not_available|overbought=overbought_not_available|time=time_1000_1200`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_lt60_source_", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_combo_entry_spot_score_score_lt60_source_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 68. `order_lifecycle_entry_bucket_liquidity_bucket_liquidity_not_available`

- title: LDM entry bucket attribution follow-up: liquidity_bucket=liquidity_not_available
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_6`, `bucket_type=liquidity_bucket`, `bucket_key=liquidity_not_available`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_entry_bucket_liquidity_bucket_liquidity_not_available", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_liquidity_bucket_liquidity_not_available", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 69. `order_lifecycle_entry_bucket_overbought_bucket_overbought_not_available`

- title: LDM entry bucket attribution follow-up: overbought_bucket=overbought_not_available
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_7`, `bucket_type=overbought_bucket`, `bucket_key=overbought_not_available`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_lifecycle_entry_bucket_overbought_bucket_overbought_not_available", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_overbought_bucket_overbought_not_availabl", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 70. `order_lifecycle_entry_bucket_score_band_score_lt60`

- title: LDM entry bucket attribution follow-up: score_band=score_lt60
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_8`, `bucket_type=score_band`, `bucket_key=score_lt60`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_entry_bucket_score_band_score_lt60", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_score_band_score_lt60", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 71. `order_lifecycle_entry_bucket_source_stage_scalp_entry_action_decision_snapshot`

- title: LDM entry bucket attribution follow-up: source_stage=scalp_entry_action_decision_snapshot
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_9`, `bucket_type=source_stage`, `bucket_key=scalp_entry_action_decision_snapshot`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_entry_bucket_source_stage_scalp_entry_action_decision_snapshot", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_source_stage_scalp_entry_action_decision_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 72. `order_lifecycle_entry_bucket_stale_bucket_stale_not_available`

- title: LDM entry bucket attribution follow-up: stale_bucket=stale_not_available
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `lifecycle_decision_matrix_entry_bucket_attribution`
- lifecycle_stage: `entry`
- target_subsystem: `lifecycle_decision_matrix`
- route: `existing_family`
- mapped_family: `lifecycle_decision_matrix_runtime`
- threshold_family: `lifecycle_decision_matrix_runtime`
- improvement_type: `entry_bucket_source_quality_attribution`
- confidence: `daily_ldm_source`
- priority: `5`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Keep entry bucket EV attribution, source-quality gaps, and threshold-cycle approval candidates connected without mutating intraday thresholds or broker submission.
- evidence: `workorder_id=entry_bucket_unknown_source_quality_10`, `bucket_type=stale_bucket`, `bucket_key=stale_not_available`, `reason=unknown_bucket_source_quality_blocker`, `recommended_route=source_quality_workorder`, `metric_role=source_quality_gate`, `decision_authority=adm_ldm_entry_bucket_attribution_source_only`, `primary_decision_metric=source_quality_adjusted_ev_pct`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: lifecycle_decision_matrix.entry_bucket_attribution should reduce unknown buckets, keep runtime_approval_candidates visible in threshold EV/runtime summary, and regenerate this workorder when source-quality confirmation is still needed.
- files_likely_touched: `src/engine/lifecycle_decision_matrix.py`, `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/report-based-automation-traceability.md`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_lifecycle_decision_matrix.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`, `postclose verifier fails if LDM entry bucket candidates/workorders are not propagated`
- implementation_status: `implemented`
- root_cause_closure_status: `root_cause_closed`
- implementation_provenance: `{"recommended_resolution": "none", "source_field_coverage": {}, "unknown_dimension_counts": {}, "unknown_reason_counts": {}}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_lifecycle_entry_bucket_stale_bucket_stale_not_available", "repeat_signature": "sig:lifecycle_decision_matrix_entry_bucket_attribution|lifecycle_decision_matrix|entry|entry_bucket_source_quality_attribution|lifecycle_decision_matrix_runtime|ldm_entry_bucket_attribution_follow_up_stale_bucket_stale_not_available", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 73. `order_conversion_lane_submit_drought_submit_drought_upstream_gate`

- title: Conversion lane blocker follow-up: submit_drought submit_drought:UPSTREAM_GATE
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_submit_drought_blocker`
- confidence: `-`
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=submit_drought:UPSTREAM_GATE`, `blocker_class=submit_drought`, `conversion_impact_rank=6`, `next_repair_action=close_submit_drought_upstream_gate`, `acceptance_test=submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "UPSTREAM_GATE", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "submit drought ledger splits LATENCY_PRE_SUBMIT/BROKER_RECEIPT/BUDGET_PASS_COLLAPSE/SIM_REAL_AUTHORITY/SOURCE_TAXONOMY_LEAKAGE/UPSTREAM_GATE", "root_cause_next_repair_action": "close_submit_drought_upstream_gate", "root_cause_signal": "conversion_lane:submit_drought:UPSTREAM_GATE:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_submit_drought_submit_drought_upstream_gate", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_submit_drought_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_submit_drought_submit_drought_upstream_gate", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 74. `order_panic_sell_defense_lifecycle_transition_pack`

- title: panic sell defense lifecycle transition pack
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `threshold_cycle_calibration_source_bundle`
- lifecycle_stage: `holding_exit`
- target_subsystem: `panic_sell_defense`
- route: `existing_family`
- mapped_family: `panic_sell_defense`
- threshold_family: `panic_sell_defense`
- improvement_type: `runtime_transition_design`
- confidence: `consensus`
- priority: `6`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Use panic-sell simulation and post-sell rebound evidence to propose threshold/guard changes, then request explicit live-runtime approval without mutating exits automatically.
- evidence: `panic_state=NORMAL`, `panic_regime_mode=NORMAL`, `stop_loss_exit_count=0`, `confirmation_eligible_exit_count=0`, `active_sim_probe_positions=3`, `post_sell_rebound_above_sell_10_20m_pct=0.0`, `microstructure_market_risk_state=RISK_OFF`, `microstructure_confirmed_risk_off_advisory=False`, `microstructure_portfolio_local_risk_off_only=False`, `market_breadth_followup_candidate=False`, `source_quality_blockers=[]`, `candidate_status={'panic_entry_freeze_guard': 'inactive_no_panic', 'panic_stop_confirmation': 'hold_no_eligible_exit', 'panic_rebound_probe': 'hold_until_recovery_confirmed', 'panic_attribution_pack': 'active_report_only'}`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: panic_sell_defense should expose simulation EV, rollback guard, approval artifact status, market/breadth confirmation, and candidate-specific threshold recommendations before any runtime transition.
- files_likely_touched: `src/engine/panic_sell_defense_report.py`, `src/engine/daily_threshold_cycle_report.py`, `src/engine/runtime_approval_summary.py`, `docs/plan-korStockScanPerformanceOptimization.rebase.md`
- acceptance_tests: `pytest panic sell defense/report lifecycle tests`, `pytest src/tests/test_build_code_improvement_workorder.py src/tests/test_runtime_approval_summary.py`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "report_only_source_bundle", "implementation_type": "panic_lifecycle_report_only_source_bundle", "panic_regime_mode": "NORMAL", "panic_state": "NORMAL", "runtime_effect": false, "source_metric_key": "panic_sell_defense", "source_quality_blockers": [], "source_report_type": "threshold_cycle_calibration_source_bundle"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 7, "repeat_key": "order_panic_sell_defense_lifecycle_transition_pack", "repeat_signature": "sig:threshold_cycle_calibration_source_bundle|panic_sell_defense|holding_exit|runtime_transition_design|panic_sell_defense|panic_sell_defense_lifecycle_transition_pack", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 75. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_dfc8a45c`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `7`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_pyramid_`, `blocker_class=source_quality`, `conversion_impact_rank=7`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_dfc8a45c", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 76. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_672cfe14`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `8`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_ai_confirmed_stale_fresh_liquidity_liquidi`, `blocker_class=source_quality`, `conversion_impact_rank=8`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_672cfe14", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 77. `order_partial_only_표류_전용_timeout_report_only`

- title: partial-only 표류 전용 timeout report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- route: `existing_family`
- mapped_family: `bad_entry_refined_canary`
- threshold_family: `bad_entry_refined_canary`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `8`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': '1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리', 'risk': 'full fill 전 짧은 대기 케이스를 오분류할 수 있음', 'required_sample': 'partial-only 코호트 20건 이상', 'metric': 'partial-only held_sec 중앙값, timeout 이후 실현손익 분포', 'apply_stage': 'report_only_observation'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_report_only_observation_contract", "implemented_scope": "bad_entry_refined_partial_only_timeout_report_contract", "runtime_effect": false, "sample_status": "contract_defined_waiting_sample", "source_contract": "bad_entry_refined_partial_only_timeout_report_contract_v1", "source_fields": ["expected_effect", "risk", "required_sample", "metric", "apply_stage"], "source_metric_snapshot": {"apply_stage": "report_only_observation", "expected_effect": "1주 partial만 남긴 채 장시간 표류하는 케이스 조기 정리", "mapped_family": "bad_entry_refined_canary", "metric": "partial-only held_sec 중앙값, timeout 이후 실현손익 분포", "required_sample": "partial-only 코호트 20건 이상", "risk": "full fill 전 짧은 대기 케이스를 오분류할 수 있음"}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_partial_only_표류_전용_timeout_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||partial_only_표류_전용_timeout_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 78. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_d8d36b81`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `9`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_level1_entry_observed_stal`, `blocker_class=source_quality`, `conversion_impact_rank=9`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 79. `order_split_entry_rebase_수량_정합성_report_only_감사`

- title: split-entry rebase 수량 정합성 report-only 감사
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- route: `existing_family`
- mapped_family: `bad_entry_refined_canary`
- threshold_family: `bad_entry_refined_canary`
- improvement_type: `threshold_family_input`
- confidence: `solo`
- priority: `9`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve EV attribution and prepare bounded calibration input.
- evidence: `{'expected_effect': 'rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함', 'risk': 'false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능', 'required_sample': 'rebase_integrity_flag 케이스 20건 이상', 'metric': 'cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포', 'apply_stage': 'report_only_observation'}`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `implementation_done`
- implementation_provenance: `{"allowed_runtime_apply": false, "decision_authority": "pattern_lab_analysis_workorder_source_only", "implementation_type": "pattern_lab_report_only_observation_contract", "implemented_scope": "bad_entry_refined_rebase_integrity_report_contract", "runtime_effect": false, "sample_status": "contract_defined_waiting_sample", "source_contract": "bad_entry_refined_rebase_integrity_report_contract_v1", "source_fields": ["expected_effect", "risk", "required_sample", "metric", "apply_stage"], "source_metric_snapshot": {"apply_stage": "report_only_observation", "expected_effect": "rebase quantity 이상(cum_gt_requested / same_ts_multi_rebase) 케이스를 분리해 실제 경제 손실과 이벤트 복원 오류를 혼합하지 않게 함", "mapped_family": "bad_entry_refined_canary", "metric": "cum_filled_qty > requested_qty 비율, same_ts_multi_rebase_count 분포", "required_sample": "rebase_integrity_flag 케이스 20건 이상", "risk": "false-positive 제거 전 손절 임계값 튜닝 시 결론 왜곡 가능"}, "source_report_type": "scalping_pattern_lab_automation"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_split_entry_rebase_수량_정합성_report_only_감사", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||split_entry_rebase_수량_정합성_report_only_감사", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 80. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_b9d53abf`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_none_exit_ex`, `blocker_class=source_quality`, `conversion_impact_rank=10`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_b9d53abf", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 81. `order_pattern_lab_ai_review_scalp_entry_adm_source_quality_below_floor`

- title: Pattern Lab AI review follow-up: scalp_entry_adm_source_quality_below_floor
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `pattern_lab_ai_review`
- lifecycle_stage: `pattern_lab_ai_review`
- target_subsystem: `pattern_lab`
- route: `existing_family`
- mapped_family: `-`
- threshold_family: `-`
- improvement_type: `source_quality_gap`
- confidence: `ai_two_pass_review`
- priority: `10`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `True`
- tuning_axis_effect: `False`
- expected_ev_effect: Improve pattern lab feedback quality without runtime mutation.
- evidence: `review_id=scalp_entry_adm_source_quality_below_floor`, `domain=scalping`, `final_state=source_quality_gap`, `final_decision=block_runtime_use`, `auditor_pass=False`, `explicit_gap_type=source_quality_gap`, `source_paths=['/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-08-04.json', '/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-04.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-04.json', '/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-04.json']`
- parity_contract: -
- next_postclose_metric: pattern_lab_ai_review.scalp_entry_adm_source_quality_below_floor
- files_likely_touched: `src/engine/pattern_lab_ai_review.py`, `src/engine/pattern_lab_currentness_audit.py`, `analysis/gemini_scalping_pattern_lab`, `analysis/claude_scalping_pattern_lab`, `analysis/deepseek_swing_pattern_lab`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest -q src/tests/test_pattern_lab_ai_review.py src/tests/test_pattern_lab_currentness_audit.py`
- implementation_status: `implemented_but_waiting_sample`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"actual_order_submitted": false, "allowed_runtime_apply": false, "blocked_reasons": ["joined_sample_below_sample_floor"], "broker_order_forbidden": true, "decision_authority": "pattern_lab_ai_review_source_only", "forbidden_uses": ["threshold mutation", "order guard mutation", "provider change", "bot restart", "broker order submit", "runtime env apply", "real order enable"], "implementation_type": "pattern_lab_scalp_entry_adm_sample_floor_provenance", "implemented_scope": "The Pattern Lab AI review workorder now preserves the ADM source contract, observed joined sample, sample floor, and deterministic block reason as source-only provenance.", "metric_role": "source_quality_gate", "normalized_review_id": "scalp_entry_adm_source_quality_below_floor", "primary_decision_metric": "source_quality_gate", "requires_separate_runtime_apply_candidate": true, "review_id": "scalp_entry_adm_source_quality_below_floor", "root_cause_closure_status_hint": "handoff_closed_root_cause_open", "runtime_effect": false, "runtime_mutation_allowed": false, "sample_count": 5, "sample_floor": 20, "sample_floor_status": "hold_sample", "source_contract_id": "scalp_entry_adm_pattern_lab_source_quality", "source_contract_status": "implemented", "source_contract_version": "scalp_entry_adm_pattern_lab_source_quality_v1", "source_paths": ["/home/ubuntu/KORStockScan/data/report/scalping_pattern_lab_automation/scalping_pattern_lab_automation_2026-08-04.json", "/home/ubuntu/KORStockScan/data/report/pattern_lab_currentness_audit/pattern_lab_currentness_audit_2026-08-04.json", "/home/ubuntu/KORStockScan/data/report/lifecycle_decision_matrix/lifecycle_decision_matrix_2026-08-04.json", "/home/ubuntu/KORStockScan/data/report/lifecycle_bucket_discovery/lifecycle_bucket_discovery_2026-08-04.json"], "source_quality_gate": "joined_sample_meets_floor_and_required_actions_present", "source_report_type": "scalping_pattern_lab_automation", "window_policy": "same_day_adm_report_plus_postclose_pattern_lab"}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented_but_waiting_sample and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 82. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_66f70bfc`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `11`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_lt60_source_ai_confirmed_stale_fresh_liquidity_liquidit`, `blocker_class=source_quality`, `conversion_impact_rank=11`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_66f70bfc", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 83. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_missing_34da627e`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `12`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_missing_submit_submit_missing_holding_holding_missing_scale_in_scale_in_arm_avg_down`, `blocker_class=source_quality`, `conversion_impact_rank=12`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 84. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_5db76271`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `13`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_sim_panic_level1_entry_observed_stal`, `blocker_class=source_quality`, `conversion_impact_rank=13`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 85. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_8d6ed15d`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `14`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_entry_action_decision_snapshot_stale`, `blocker_class=source_quality`, `conversion_impact_rank=14`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 86. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_c06eb6b2`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `15`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_63_65_source_scalp_sim_panic_bottoming_entry_allowed_st`, `blocker_class=source_quality`, `conversion_impact_rank=15`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 87. `order_conversion_lane_bridge_contract_entry_wait6579_score66_69_recovery_gate_v1_2026_08_04`

- title: Conversion lane blocker follow-up: bridge_contract entry_wait6579_score66_69_recovery_gate_v1:2026-08-04
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_bridge_contract_blocker`
- confidence: `-`
- priority: `16`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=entry_wait6579_score66_69_recovery_gate_v1:2026-08-04`, `blocker_class=bridge_contract`, `conversion_impact_rank=16`, `next_repair_action=bridge_contract`, `acceptance_test=runtime_apply_bridge emits explicit bridge blocker ledger or live_auto_apply_ready`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "bridge_contract", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "runtime_apply_bridge emits explicit bridge blocker ledger or live_auto_apply_ready", "root_cause_next_repair_action": "bridge_contract", "root_cause_signal": "conversion_lane:bridge_contract:bridge_contract:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 88. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_bbd448af`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `17`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_60_62_source_scalp_sim_panic_level1_entry_observed_stal`, `blocker_class=source_quality`, `conversion_impact_rank=17`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 89. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_437582bf`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai_confirmed_stale_fresh_liquidity_liquidi
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `18`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_ai_confirmed_stale_fresh_liquidity_liquidi`, `blocker_class=source_quality`, `conversion_impact_rank=18`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 90. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_7868f88a`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `19`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_blocked_ai_score_stale_fresh_liquidity_liq`, `blocker_class=source_quality`, `conversion_impact_rank=19`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

### 91. `order_conversion_lane_source_quality_lifecycle_flow_combo_lifecycle_flow_entry_entry_combo_en_e815cc58`

- title: Conversion lane blocker follow-up: source_quality lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `conversion_lane`
- lifecycle_stage: `conversion`
- target_subsystem: `sim_to_real_conversion_lineage`
- route: `existing_family`
- mapped_family: `sim_to_real_conversion_lane`
- threshold_family: `sim_to_real_conversion_lane`
- improvement_type: `conversion_source_quality_blocker`
- confidence: `-`
- priority: `20`
- runtime_effect: `False`
- strategy_effect: `False`
- data_quality_effect: `False`
- tuning_axis_effect: `False`
- expected_ev_effect: reduce remaining blocker count before bounded real canary can be requested
- evidence: `conversion_candidate_id=lifecycle_flow:combo_lifecycle_flow:entry_entry_combo_entry_spot_score_score_66_69_source_scalp_entry_action_decision_snapshot_stale`, `blocker_class=source_quality`, `conversion_impact_rank=20`, `next_repair_action=source_quality`, `acceptance_test=source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass`, `runtime_effect=false`, `allowed_runtime_apply=false`
- parity_contract: -
- next_postclose_metric: -
- files_likely_touched: `src/engine/automation/key_lineage_ledger.py`, `src/engine/automation/conversion_lane.py`, `src/engine/verify_threshold_cycle_postclose_chain.py`, `src/engine/build_code_improvement_workorder.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_conversion_lane_key_lineage.py src/tests/test_build_code_improvement_workorder.py src/tests/test_verify_threshold_cycle_postclose_chain.py`
- implementation_status: `implemented`
- root_cause_closure_status: `handoff_closed_root_cause_open`
- implementation_provenance: `{"allowed_runtime_apply": false, "blocker_axis": "lifecycle_flow:combo_lifecycle_flow", "blocker_resolution_status": "open", "implementation_status": "implemented", "implemented_scope": "conversion_lane_blocker_axis_report_provenance", "remaining_blocker_is_observation_or_policy_closure": true, "root_cause_acceptance_test": "source-quality audit excludes/fixes defective rows and candidate source_quality_state becomes pass", "root_cause_next_repair_action": "source_quality", "root_cause_signal": "conversion_lane:source_quality:lifecycle_flow:combo_lifecycle_flow:open", "runtime_effect": false}`
- repeat_unresolved_escalation: `-`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented", "previous_route": "existing_family", "repeat_count": 3, "repeat_key": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "repeat_signature": "sig:conversion_lane|sim_to_real_conversion_lineage|conversion|conversion_source_quality_blocker|sim_to_real_conversion_lane|conversion_lane_blocker_follow_up_source_quality_lifecycle_flow_combo_lifecycle_", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- structural_blocker_escalation: `-`
- automation_reentry: Next postclose workorder should preserve implementation_status=implemented and use the source metrics as provenance only.

실행 기준:

- 기존 threshold family의 source metric/provenance를 보강한다.
- 다음 intraday/postclose calibration에서 해당 family 입력으로 소비되어야 한다.
- family state/value 변경은 deterministic guard와 auto_bounded_live 체인을 통해서만 가능하다.

## Non-Selected Source Orders

아래 항목은 source order로 분류됐지만 selected implementation order에는 포함되지 않았다. 재작업 지시 시 `decision`, `decision_reason`, `runtime_effect`를 먼저 재판정한다.

### N1. `order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only`

- title: 동일 종목 split-entry soft-stop 재진입 cooldown report-only
- decision: `attach_existing_family`
- decision_reason: instrumentation/report/provenance implementation status is implemented_but_waiting_sample; keep the order as existing-family source evidence instead of re-implementing
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `implemented_but_waiting_sample`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "attach_existing_family", "previous_implementation_status": "implemented_but_waiting_sample", "previous_route": "existing_family", "repeat_count": 5, "repeat_key": "order_동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "repeat_signature": "sig:scalping_pattern_lab_automation|holding_exit||threshold_family_input||동일_종목_split_entry_soft_stop_재진입_cooldown_report_only", "review_disposition": "implemented_with_provenance"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N2. `order_no_acute_observability_alert`

- title: No acute observability alert
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `scalping_logic`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 4, "repeat_key": "order_no_acute_observability_alert", "repeat_signature": "sig:scalping_pattern_lab_automation|scalping_logic||no_acute_observability_alert||no_acute_observability_alert", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N3. `order_liquidity_gate_miss_ev_recovery`

- title: liquidity gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 5, "repeat_key": "order_liquidity_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||liquidity_gate_miss_ev_recovery||liquidity_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N4. `order_overbought_gate_miss_ev_recovery`

- title: overbought gate miss EV recovery
- decision: `design_family_candidate`
- decision_reason: pattern lab can only propose source-only family design input; LDM/discovery/runtime bridge contracts must close before any auto_bounded_live consideration
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `entry_filter_quality`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_design_family_candidate`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "design_family_candidate", "previous_implementation_status": "terminal_design_family_candidate", "previous_route": "auto_family_candidate", "repeat_count": 5, "repeat_key": "order_overbought_gate_miss_ev_recovery", "repeat_signature": "sig:scalping_pattern_lab_automation|entry_filter_quality||overbought_gate_miss_ev_recovery||overbought_gate_miss_ev_recovery", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

### N5. `order_scalp_entry_adm_daily_tuning_coverage`

- title: scalp entry ADM daily tuning coverage
- decision: `defer_evidence`
- decision_reason: Entry ADM warning is waiting on clean sample/runtime observation, not a code implementation gap
- source_report_type: `threshold_cycle_ev`
- lifecycle_stage: `entry`
- target_subsystem: `entry_funnel`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_deferred_evidence`
- longstanding_non_implement_review: `{"history_window_days": 10, "previous_decision": "defer_evidence", "previous_implementation_status": "terminal_deferred_evidence", "previous_route": "instrumentation_order", "repeat_count": 7, "repeat_key": "order_scalp_entry_adm_daily_tuning_coverage", "repeat_signature": "sig:threshold_cycle_ev|entry_funnel|entry|instrumentation_report_provenance|scalp_entry_action_decision_matrix_advisory|scalp_entry_adm_daily_tuning_coverage", "review_disposition": "review_required"}`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/scalp_entry_action_decision_matrix.py`, `src/engine/sniper_state_handlers.py`, `src/engine/scalp_entry_adm_runtime.py`, `src/engine/threshold_cycle_ev_report.py`
- acceptance_tests: `PYTHONPATH=. .venv/bin/pytest src/tests/test_scalp_entry_action_decision_matrix.py src/tests/test_build_code_improvement_workorder.py`, `runtime_effect remains false and broker submit safety guards remain owner`

### N6. `order_partial_fallback_확대_직후_즉시_재평가_report_only`

- title: partial → fallback 확대 직후 즉시 재평가 report-only
- decision: `reject`
- decision_reason: fallback revival or shadow reintroduction conflicts with current Plan Rebase policy
- source_report_type: `scalping_pattern_lab_automation`
- lifecycle_stage: `-`
- target_subsystem: `holding_exit`
- runtime_effect: `False`
- allowed_runtime_apply: `False`
- implementation_status: `terminal_rejected`
- longstanding_non_implement_review: `-`
- longstanding_non_implement_action: `-`
- files_likely_touched: `src/engine/daily_threshold_cycle_report.py`, `src/engine/sniper_state_handlers.py`
- acceptance_tests: `pytest relevant report/threshold tests`, `runtime_effect remains false until a separate implementation order is completed`, `daily EV report includes the order summary`

## 자동화체인 재투입

- 구현 결과는 `2026-08-05` 이후 postclose `threshold_cycle`, `scalping_pattern_lab_automation`, `threshold_cycle_ev`가 자동으로 다시 읽는다.
- 구현자가 수동으로 threshold 값을 바꾸는 것이 아니라, source/report/provenance를 닫아 다음 calibration이 판단하게 한다.
- 다음 Codex 세션 입력 문구: `none_for_bucket_discovery_classification`

## Project/Calendar 동기화

문서/checklist를 수정했으면 parser 검증은 실행하고, Project/Calendar 동기화는 사용자가 아래 명령으로 수동 실행한다.

```bash
PYTHONPATH=. .venv/bin/python -m src.engine.sync_docs_backlog_to_project && PYTHONPATH=. .venv/bin/python -m src.engine.sync_github_project_calendar
```
